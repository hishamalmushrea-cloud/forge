#!/usr/bin/env python3
"""PoC link-level shootout — PREDICTED (pre-hardware) numbers.
FIXED vs LFSR-FHSS vs HASH-FHSS(SHA256-CTR, modern baseline) vs CHAOS-FHSS(Q16).
Attackers: NONE / BARRAGE k-of-8 / FOLLOWER (Berlekamp-Massey predictor, K=1).
Verdict encoded as asserts: blind-jam equality + follower divergence.
"""
import hashlib
import json
import pathlib
import random
import re

NCH, NSLOT, SLOT_MS = 8, 2000, 100
E_TX_MJ = 0.030 * 0.025 * 3.3 * 1000.0
rng = random.Random(1234)

# ---------- LFSR-16: x^16+x^14+x^13+x^11+1 ----------
def _fb(s):
    return ((s >> 0) & 1) ^ ((s >> 2) & 1) ^ ((s >> 3) & 1) ^ ((s >> 5) & 1)


def _period(seed=0xACE1):
    s, n = seed, 0
    while True:
        s = (s >> 1) | (_fb(s) << 15)
        n += 1
        if s == seed:
            return n
        assert n < 70000, 'LFSR not max-length'


assert _period() == 65535, 'LFSR taps wrong — fix before trusting shootout'
print('LFSR-16 period 65535 [OK]')


def gen_lfsr(n, seed=0xACE1):
    s = seed
    chs, bits = [], []
    for _ in range(n):
        c = 0
        for b in range(3):
            o = s & 1
            bits.append(o)
            c |= o << b
            s = (s >> 1) | (_fb(s) << 15)
        chs.append(c)
    return chs, bits


# ---------- Berlekamp-Massey (binary) + predictor ----------
def bm(bits):
    C, B, L, m = [1], [1], 0, 1
    for n in range(len(bits)):
        d = bits[n]
        for i in range(1, L + 1):
            if i < len(C):
                d ^= C[i] & bits[n - i]
        if d == 0:
            m += 1
            continue
        T = C[:]
        need = len(B) + m
        if len(C) < need:
            C += [0] * (need - len(C))
        for i in range(len(B)):
            C[i + m] ^= B[i]
        if 2 * L <= n:
            L, B, m = n + 1 - L, T, 1
        else:
            m += 1
    return C, L


def predict(C, L, hist, k):
    h = hist[:]
    out = []
    for _ in range(k):
        b = 0
        for i in range(1, L + 1):
            b ^= C[i] & h[-i]
        h.append(b)
        out.append(b)
    return out


# ---------- HASH-FHSS (SHA256-CTR — the fair modern baseline) ----------
def gen_hash(n, seed=b'POC-hash-seed-01'):
    chs, bits = [], []
    for c in range(n):
        v = int.from_bytes(hashlib.sha256(seed + c.to_bytes(4, 'big')).digest()[:2], 'big') % 8
        chs.append(v)
        bits += [(v >> b) & 1 for b in range(3)]
    return chs, bits


# ---------- CHAOS-FHSS (Q16 mirror of chaos_mesh.py) ----------
S = 1 << 16


def fsh(v, n):
    return v >> n if v >= 0 else -(((-v) + (1 << n) - 1) >> n)


def step(st):
    X, Y, Z = st
    X += fsh(10 * (Y - X), 7)
    Y += fsh(fsh(X * (28 * S - Z), 16) - Y, 7)
    Z += fsh(fsh(X * Y, 16) - (8 * Z) // 3, 7)
    return (X, Y, Z)


def gen_chaos(n, seed=b'FORGE-mesh-seed-01'):
    u = int.from_bytes(hashlib.sha256(seed).digest()[:8], 'big')
    st = (S + u % (40 * S), S + (u >> 3) % (40 * S), S + (u >> 5) % (40 * S))
    for _ in range(3000):
        st = step(st)
    chs, bits = [], []
    for _ in range(n):
        for _ in range(50):
            st = step(st)
        v = ((0 if st[1] > 0 else 1) * 4 + (fsh(abs(st[2]), 16) // 6) % 4) % 8
        chs.append(v)
        bits += [(v >> b) & 1 for b in range(3)]
    return chs, bits


# ---------- self-tests: BM kills LFSR, fails on random ----------
_L, _Lb = gen_lfsr(300)
_C, _L = bm(_Lb[:64])
assert _L == 16, f'BM selftest L={_L}'
assert predict(_C, _L, _Lb[:64], 236) == _Lb[64:300], 'BM must perfectly predict LFSR'
print(f'BM selftest: L={_L}, 236/236 predicted [OK]')

_H, _Hb = gen_hash(500)
_Ch, _Lh = bm(_Hb[:64])
_acc = sum(a == b for a, b in zip(predict(_Ch, _Lh, _Hb[:64], 300), _Hb[64:364])) / 300
assert _Lh > 16 and 0.35 <= _acc <= 0.65, f'random sanity L={_Lh} acc={_acc}'
print(f'Random sanity: L={_Lh}, bit-predict {_acc:.2f} (~coin) [OK]')

# ---------- generate + cross-check chaos mirror vs golden.h ----------
CHS_F = [0] * NSLOT
CHS_L, B_L = gen_lfsr(NSLOT)
CHS_H, B_H = gen_hash(NSLOT)
CHS_C, B_C = gen_chaos(NSLOT)
gold = list(map(int, re.findall(r'\d+', (pathlib.Path(__file__).parent.parent /
                'firmware' / 'golden.h').read_text().split('{')[1].split('}')[0])))
assert gold == CHS_C, 'Q16 mirror diverged from golden.h!'
print('Q16 mirror == golden.h 2000/2000 [OK]')


# ---------- scenarios ----------
def pdr_barrage(chs, J):
    return sum(c not in J for c in chs) / len(chs)


def follower(chs):
    ok, hist, hits, att = 0, [], 0, 0
    for t in range(NSLOT):
        if len(hist) >= 66:
            Cc, Lc = bm(hist[-64:])
            pr = predict(Cc, Lc, hist, 3)
            pg = pr[0] | (pr[1] << 1) | (pr[2] << 2)
            att += 1
            hits += (pg == chs[t])
        else:
            pg = rng.randrange(8)
        ok += (pg != chs[t])
        b = chs[t]
        hist += [b & 1, (b >> 1) & 1, (b >> 2) & 1]
    return ok / NSLOT, hits / max(att, 1)


def latency(chs, J, cap=20):
    t, tot, n = 0, 0, 0
    while t < NSLOT:
        a = 1
        while a <= cap and t + a - 1 < NSLOT and chs[t + a - 1] in J:
            a += 1
        if a <= cap and t + a - 1 < NSLOT:
            tot += a
            n += 1
            t += a
        else:
            t += cap
    return (tot / n) if n else None


JSETS = {1: {0}, 2: {0, 4}, 4: {0, 1, 2, 3}, 6: {0, 1, 2, 3, 4, 5}}
SCH = {'fixed': CHS_F, 'lfsr': CHS_L, 'hash': CHS_H, 'chaos': CHS_C}
R = {'params': {'nch': NCH, 'nslot': NSLOT, 'slot_ms': SLOT_MS, 'label': 'PREDICTED pre-hardware'}}

R['pdr_none'] = {k: round(pdr_barrage(v, set()), 4) for k, v in SCH.items()}
for k, J in JSETS.items():
    R[f'pdr_bar{k}'] = {kk: round(pdr_barrage(v, J), 4) for kk, v in SCH.items()}
print('barrage done; running follower (BM per slot, ~4x2000)...')
R['pdr_foll'], R['foll_acc'] = {}, {}
for k, v in SCH.items():
    f, a = follower(v)
    R['pdr_foll'][k], R['foll_acc'][k] = round(f, 4), round(a, 4)
    print(f'  follower vs {k}: pdr={f:.3f} acc={a:.3f}')
R['lat50'] = {}
for k, v in SCH.items():
    la = latency(v, JSETS[4])
    R['lat50'][k] = round(la, 3) if la else None
R['mJ_per_delivered'] = {k: (round(v * E_TX_MJ, 3) if v else None) for k, v in R['lat50'].items()}
order, true = [0, 1, -1, 2, -2], round(3000 * 500e-6)
R['resync_slots'] = {'fixed': 'N/A', 'lfsr': order.index(true) + 1,
                     'hash': order.index(true) + 1, 'chaos': order.index(true) + 1}

# ---------- the scientific claims, encoded ----------
assert R['pdr_foll']['chaos'] > R['pdr_foll']['lfsr'] + 0.5, 'chaos must crush LFSR vs follower'
assert R['pdr_foll']['hash'] > 0.7 and R['pdr_foll']['chaos'] > 0.7, 'unpredictable must survive'
assert abs(R['pdr_bar4']['chaos'] - R['pdr_bar4']['lfsr']) < 0.08, 'blind-jam equality expected'
assert abs(R['pdr_bar4']['chaos'] - R['pdr_bar4']['hash']) < 0.08, 'blind-jam equality expected'

json.dump(R, open(pathlib.Path(__file__).parent / 'predicted.json', 'w'), indent=1)


def pct(x):
    return '—' if x is None else f'{100 * x:.1f}%'


print('\n| Test | Fixed | LFSR | Hash | Chaos |')
print('|---|---|---|---|---|')
print(f"| PDR no-jam | {pct(R['pdr_none']['fixed'])} | {pct(R['pdr_none']['lfsr'])} | {pct(R['pdr_none']['hash'])} | {pct(R['pdr_none']['chaos'])} |")
for k in (1, 2, 4, 6):
    r = R[f'pdr_bar{k}']
    print(f"| PDR barrage {k}/8 | {pct(r['fixed'])} | {pct(r['lfsr'])} | {pct(r['hash'])} | {pct(r['chaos'])} |")
print(f"| PDR follower K=1 | {pct(R['pdr_foll']['fixed'])} | {pct(R['pdr_foll']['lfsr'])} | {pct(R['pdr_foll']['hash'])} | {pct(R['pdr_foll']['chaos'])} |")
print(f"| Follower predict-acc | {pct(R['foll_acc']['fixed'])} | {pct(R['foll_acc']['lfsr'])} | {pct(R['foll_acc']['hash'])} | {pct(R['foll_acc']['chaos'])} |")
L = R['lat50']
print(f"| Latency@50% (ms) | {'∞' if L['fixed'] is None else round(L['fixed']*SLOT_MS,1)} | {round(L['lfsr']*SLOT_MS,1)} | {round(L['hash']*SLOT_MS,1)} | {round(L['chaos']*SLOT_MS,1)} |")
E = R['mJ_per_delivered']
print(f"| mJ/delivered@50% | {'∞' if E['fixed'] is None else E['fixed']} | {E['lfsr']} | {E['hash']} | {E['chaos']} |")
S5 = R['resync_slots']
print(f"| Resync slots | {S5['fixed']} | {S5['lfsr']} | {S5['hash']} | {S5['chaos']} |")
print('\nALL HYPOTHESIS ASSERTS PASS — predictions written to poc/predicted.json')
