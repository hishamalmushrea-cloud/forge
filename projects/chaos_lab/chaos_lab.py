#!/usr/bin/env python3
"""MUSHREA FORGE — Chaos lab: Lorenz-63 RNG + stream cipher demo + statistical tests (stdlib only).

CORE: Lorenz s=10,r=28,b=8/3, RK4 dt=0.01, warmup 3000, sample every 25 steps, bit=sign(x),
  Von Neumann debiasing. Seed 128-bit -> (x0,y0,z0,offset).
TESTS: monobit, runs, byte-entropy, avalanche (1-bit seed flip -> ~50%), encrypt roundtrip.
STATUS: EXECUTED + VERIFIED here. Educational crypto only (see R5/F1/F2).
"""
import json, math, random

S, R, B, DT = 10.0, 28.0, 8.0 / 3.0, 0.01
WARM, EVERY, RAW_N = 3000, 100, 60000  # EVERY=100: decorrelate wing residence (~time units)

def rk4(s):
    x, y, z = s
    def f(p):
        return (S * (p[1] - p[0]), p[0] * (R - p[2]) - p[1], p[0] * p[1] - B * p[2])
    def add(p, k, h):
        return (p[0] + k[0] * h, p[1] + k[1] * h, p[2] + k[2] * h)
    k1 = f(s); k2 = f(add(s, k1, DT / 2)); k3 = f(add(s, k2, DT / 2)); k4 = f(add(s, k3, DT))
    return (x + (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]) * DT / 6,
            y + (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1]) * DT / 6,
            z + (k1[2] + 2 * k2[2] + 2 * k3[2] + k4[2]) * DT / 6)

def seed_to_state(seed128):
    r = random.Random(seed128)
    return (r.uniform(-15, 15), r.uniform(-15, 15), r.uniform(5, 40))

def raw_bits(seed128, n):
    s = seed_to_state(seed128)
    for _ in range(WARM):
        s = rk4(s)
    out = []
    for _ in range(n):
        for _ in range(EVERY):
            s = rk4(s)
        out.append(1 if s[0] > 0 else 0)
    return out

def von_neumann(bits):
    out = []
    for i in range(0, len(bits) - 1, 2):
        a, b = bits[i], bits[i + 1]
        if a != b:
            out.append(a)
    return out

def monobit(bits):
    n = len(bits)
    p = sum(bits) / n
    lo, hi = 0.5 - 3 * 0.5 / math.sqrt(n), 0.5 + 3 * 0.5 / math.sqrt(n)
    return p, lo <= p <= hi

def runs_test(bits):
    n = len(bits)
    runs = 1 + sum(1 for i in range(1, n) if bits[i] != bits[i - 1])
    exp, sd = (n + 1) / 2, math.sqrt((n - 1) / 4)  # binary runs, p=0.5
    return runs, abs(runs - exp) <= 3 * sd

def byte_entropy(bits):
    n8 = len(bits) // 8 * 8
    freq = [0] * 256
    for i in range(0, n8, 8):
        v = 0
        for k in range(8):
            v = (v << 1) | bits[i + k]
        freq[v] += 1
    ent = -sum((c / (n8 / 8)) * math.log2(c / (n8 / 8)) for c in freq if c)
    return ent, ent > 7.7

SEED = 0xC0FFEE1234567890ABCDEF9876543210
raw = raw_bits(SEED, RAW_N)
bits = von_neumann(raw)
p, ok_m = monobit(bits)
runs, ok_r = runs_test(bits)
ent, ok_e = byte_entropy(bits)
# determinism + avalanche
bits2 = von_neumann(raw_bits(SEED, RAW_N))
rawB = raw_bits(SEED ^ 1, 6000)
diff = sum(a != b for a, b in zip(raw[:6000], rawB)) / 6000
# roundtrip demo
msg = b"FORGE-CHAOS"
ks = von_neumann(raw_bits(SEED, 4096))[:len(msg) * 8]
ct = bytes(m ^ int("".join(map(str, ks[i * 8:(i + 1) * 8])), 2) for i, m in enumerate(msg))
ks2 = von_neumann(raw_bits(SEED, 4096))[:len(msg) * 8]
pt = bytes(c ^ int("".join(map(str, ks2[i * 8:(i + 1) * 8])), 2) for i, c in enumerate(ct))

res = {"seed": hex(SEED), "raw_n": RAW_N, "debiased_n": len(bits),
       "monobit_p": round(p, 4), "monobit_pass": ok_m,
       "runs": runs, "runs_pass": ok_r,
       "byte_entropy": round(ent, 3), "entropy_pass": ok_e,
       "deterministic": bits == bits2,
       "avalanche_diff": round(diff, 4),
       "roundtrip_ok": pt == msg, "ciphertext_hex": ct.hex()}
with open("results.json", "w") as f:
    json.dump(res, f, indent=1)

# ---- SVG: Lorenz x-z butterfly ----
s = seed_to_state(SEED)
for _ in range(WARM):
    s = rk4(s)
pts = []
for _ in range(3000):
    for _ in range(4):
        s = rk4(s)
    pts.append((s[0], s[2]))
W, H, PL, PB, PT, PR = 660, 460, 40, 40, 40, 20
X = lambda v: PL + (v + 22) / 44 * (W - PL - PR)
Y = lambda v: (H - PB) - v / 50 * (H - PB - PT)
g = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" font-family="sans-serif">' % (W, H),
     '<rect width="%d" height="%d" fill="#0b1220"/>' % (W, H),
     '<text x="%d" y="22" text-anchor="middle" font-size="14" font-weight="bold" fill="white">Lorenz butterfly (x-z) — our RNG core, EXECUTED</text>' % (W // 2),
     '<text x="%d" y="%d" text-anchor="middle" font-size="11" fill="#7dd3fc">monobit p=%.4f %s | entropy %.2f/8 %s | avalanche %.1f%%</text>'
     % (W // 2, H - 8, p, "PASS" if ok_m else "FAIL", ent, "PASS" if ok_e else "FAIL", diff * 100)]
g.append('<polyline points="%s" fill="none" stroke="#38bdf8" stroke-width="1" opacity="0.75"/>' %
         " ".join("%.1f,%.1f" % (X(a), Y(b)) for a, b in pts))
g.append('</svg>')
with open("chart.svg", "w") as f:
    f.write("\n".join(g))

print(f"bits={len(bits)} monobit p={p:.4f} {'PASS' if ok_m else 'FAIL'} | runs={runs} {'PASS' if ok_r else 'FAIL'} | entropy={ent:.3f} {'PASS' if ok_e else 'FAIL'}")
print(f"deterministic={bits == bits2} avalanche={diff*100:.1f}% roundtrip={pt == msg} ct={ct.hex()}")
print("wrote results.json + chart.svg [EXECUTED]")
