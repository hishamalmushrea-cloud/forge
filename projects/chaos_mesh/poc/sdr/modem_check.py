#!/usr/bin/env python3
"""Reference MODEM check (pure python, no RF): 2FSK + packet + CRC, clean vs jammed."""
import math
import pathlib
import random
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from pktutil import build, parse, gen_chaos  # noqa: E402

FS, F0, F1, SPS = 8000.0, 1200.0, 2200.0, 8
KEY = b'pair-key-16bytes'


def mod(bits):
    out = []
    for b in bits:
        f = F1 if b else F0
        out += [math.cos(2 * math.pi * f * (i / FS)) for i in range(SPS)]
    return out


def demod(samp):
    bits = []
    for s in range(0, len(samp), SPS):
        e = []
        for f in (F0, F1):
            ci = sum(samp[s + i] * math.cos(2 * math.pi * f * i / FS) for i in range(SPS))
            cq = sum(samp[s + i] * math.sin(2 * math.pi * f * i / FS) for i in range(SPS))
            e.append(ci * ci + cq * cq)
        bits.append(1 if e[1] > e[0] else 0)
    return bits


def tobits(pkt):
    return [(b >> k) & 1 for b in pkt for k in range(7, -1, -1)]


def tobytes(bits):
    return bytes(sum(bits[i + k] << (7 - k) for k in range(8)) for i in range(0, len(bits), 8))


def trial(rng, jam_tone, n=200):
    per = 0
    for t in range(n):
        pkt = build(t, bytes([t & 0xFF]) * 8, KEY)
        s = mod(tobits(pkt))
        s = [v + rng.gauss(0, 0.15) + jam_tone * math.cos(2 * math.pi * F1 * i / FS)
             for i, v in enumerate(s)]
        ok = parse(tobytes(demod(s)), KEY)
        per += (ok is None or ok[0] != t)
    return per / n


# engine cross-check vs golden.h
gold = list(map(int, re.findall(r'\d+', (pathlib.Path(__file__).parent.parent.parent /
                'firmware' / 'golden.h').read_text().split('{')[1].split('}')[0])))
assert gen_chaos(b'FORGE-mesh-seed-01', 2000) == gold, 'pktutil engine diverged!'
print('pktutil engine == golden.h 2000/2000 [OK]')

rng = random.Random(7)
clean = trial(rng, 0.0)
jammed = trial(rng, 3.0)
print(f'PER clean={clean:.3f} jammed={jammed:.3f}')
assert clean <= 0.01 and jammed >= 0.80, 'modem sanity failed'
print('MODEM CHECK PASS')
