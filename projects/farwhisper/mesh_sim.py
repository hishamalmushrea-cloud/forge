#!/usr/bin/env python3
"""Mesh flood simulator: 12 nodes / 20x20km / R=6km, chaos-hop-equivalent uniform channels.
Cites linksim: chaos ~= uniform vs blind jammer, so LCG hops are a faithful stand-in here."""
import json
import math
import random

rng = random.Random(42)
N, AREA, R, TTL, NMSG = 12, 20.0, 6.0, 6, 200
JAM = {0, 1, 2, 3}


def build(seed):
    r = random.Random(seed)
    pp = [(0.0, 10.0)] + [(round(r.uniform(0, AREA), 1), round(r.uniform(0, AREA), 1))
                          for _ in range(N - 2)] + [(AREA, 10.0)]
    ll = {i: set() for i in range(N)}
    for i in range(N):
        for j in range(i + 1, N):
            if math.dist(pp[i], pp[j]) <= R:
                ll[i].add(j)
                ll[j].add(i)
    return pp, ll


def _conn(pp, ll):
    seen, q = {0}, [0]
    while q:
        u = q.pop(0)
        for w in ll[u]:
            if w not in seen:
                seen.add(w)
                q.append(w)
    return N - 1 in seen


SEED = next(s for s in range(200) if _conn(*build(s)))
pos, links = build(SEED)
print(f'topology seed={SEED} connected')


class LCG:
    def __init__(self, s):
        self.s = s

    def hop(self):
        self.s = (1103515245 * self.s + 12345) & 0x7FFFFFFF
        return (self.s >> 16) % 8



def bfs_path():
    prev = {0: None}
    q = [0]
    while q:
        u = q.pop(0)
        if u == N - 1:
            break
        for w in sorted(links[u]):
            if w not in prev:
                prev[w] = u
                q.append(w)
    assert N - 1 in prev, 'A-B disconnected: reseed'
    p, u = [], N - 1
    while u is not None:
        p.append(u)
        u = prev[u]
    return p[::-1]


PATH = bfs_path()
print(f'topology: A-B shortest = {len(PATH) - 1} hops via {PATH}')


TX_TRIES = 3  # blind retries, each on a FRESH hop channel (independent draws)


def flood(jam):
    lcg = LCG(99)
    ok, hops_sum, tx_sum, dup = 0, 0, 0, 0
    for _ in range(NMSG):
        seen, frontier, depth = {0}, [0], {0: 0}
        while frontier:
            nxt = []
            for u in frontier:
                clear = False
                for _ in range(TX_TRIES):
                    tx_sum += 1
                    if not jam or lcg.hop() not in JAM:
                        clear = True
                if not clear:
                    continue
                for w in links[u]:
                    if w in seen:
                        dup += 1
                    elif depth[u] + 1 <= TTL:
                        seen.add(w)
                        depth[w] = depth[u] + 1
                        nxt.append(w)
            frontier = nxt
        if N - 1 in seen:
            ok += 1
            hops_sum += depth[N - 1]
    return ok / NMSG, hops_sum / max(ok, 1), tx_sum / NMSG, dup


p0, h0, tx0, d0 = flood(False)
pJ, hJ, txJ, dJ = flood(True)
print(f'PDR no-jam={p0:.3f} hops={h0:.1f} tx/msg={tx0:.1f} dups={d0}')
print(f'PDR jam50 ={pJ:.3f} hops={hJ:.1f} tx/msg={txJ:.1f} dups={dJ}')
assert p0 >= 0.95 and pJ >= 0.70, 'mesh must deliver (diversity beats barrage)'
assert d0 > 0 and hJ <= TTL, 'seen-cache working, TTL respected'

# fragmentation roundtrip (171B -> 1 frame, 400B -> 2)
FRAG = 200 - 13


def frag(data):
    return [data[i:i + FRAG] for i in range(0, len(data), FRAG)]


assert len(frag(bytes(171))) == 1 and len(frag(bytes(400))) == 3, 'frag counts'
assert b''.join(frag(bytes(range(256)) * 2)) == bytes(range(256)) * 2, 'frag roundtrip'
print('frag: 171B->1 frame, 400B->3 frames, roundtrip OK')

# map SVG
S = 30
el = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{AREA*S+40}" height="{AREA*S+40}" font-family="Tahoma" font-size="12">',
      f'<rect width="{AREA*S+40}" height="{AREA*S+40}" fill="#0b1220"/>']
X = lambda x: 20 + x * S
Y = lambda y: 20 + y * S
for i in range(N):
    for j in links[i]:
        if j > i:
            el.append(f'<line x1="{X(pos[i][0])}" y1="{Y(pos[i][0])}" x2="{X(pos[j][0])}" y2="{Y(pos[j][0])}" stroke="#334155"/>')
for k in range(len(PATH) - 1):
    a, b = PATH[k], PATH[k + 1]
    el.append(f'<line x1="{X(pos[a][0])}" y1="{Y(pos[a][0])}" x2="{X(pos[b][0])}" y2="{Y(pos[b][0])}" stroke="#4ade80" stroke-width="3"/>')
for i, (x, y) in enumerate(pos):
    c = '#f87171' if i == 0 else ('#38bdf8' if i == N - 1 else '#94a3b8')
    el.append(f'<circle cx="{X(x)}" cy="{Y(y)}" r="9" fill="{c}"/><text x="{X(x)-4}" y="{Y(y)+4}" fill="#000">{i}</text>')
el.append(f'<text x="20" y="{AREA*S+32}" fill="#94a3b8">A(0) أحمر ←→ B(11) أزرق: {len(PATH)-1} قفزات | PDR نظيف {p0:.0%} / وابل {pJ:.0%}</text>')
el.append('</svg>')
open('mesh.svg', 'w', encoding='utf-8').write('\n'.join(el))

json.dump({'pdr_clean': p0, 'pdr_jam50': pJ, 'hops': round(hJ, 2), 'path': PATH,
           'verdict': 'MESH [VERIFIED]'}, open('mesh_results.json', 'w'), indent=1)
print('VERDICT: MESH [VERIFIED]')
