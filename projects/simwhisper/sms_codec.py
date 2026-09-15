#!/usr/bin/env python3
"""Data-SMS codec: capsule -> 140B segments (5B header + 135B body). Golden for JS cross-check."""
import json

SEG, HDR, BODY = 140, 5, 135
VER, PORT = 0x02, 8091


def crc8(d):
    c = 0
    for b in d:
        c ^= b
        for _ in range(8):
            c = ((c << 1) ^ 0x07) & 0xFF if c & 0x80 else (c << 1) & 0xFF
    return c


def encode(cap: bytes, msgid: int):
    n = (len(cap) + BODY - 1) // BODY
    c = crc8(cap)
    return [bytes([VER, msgid & 0xFF, n, i, c]) + cap[i * BODY:(i + 1) * BODY]
            for i in range(n)]


def decode(segs):
    if not segs:
        raise ValueError('empty')
    v, mid, n, _, c = segs[0][0], segs[0][1], segs[0][2], segs[0][3], segs[0][4]
    parts = {}
    for s in segs:
        if len(s) < HDR or s[0] != v or s[1] != mid or s[2] != n or s[4] != c or s[3] >= n:
            raise ValueError('bad/mixed segment')
        parts.setdefault(s[3], s[HDR:])
    if len(parts) != n:
        raise ValueError(f'incomplete {len(parts)}/{n}')
    out = b''.join(parts[i] for i in range(n))
    if crc8(out) != c:
        raise ValueError('crc8 fail')
    return out


def text_segments(t: str):
    return 1 if len(t) <= 70 else (len(t) + 66) // 67  # UCS-2 Arabic


tests = []
cap171 = bytes((i * 7 + 1) % 256 for i in range(171))
s = encode(cap171, 9)
tests.append(('171B->2segs', len(s) == 2))
tests.append(('roundtrip-shuffled-dup', decode([s[1], s[0], s[1]]) == cap171))
s500 = encode(bytes(500), 3)
tests.append(('500B->4segs', len(s500) == 4))
try:
    bad = bytearray(s[0])
    bad[10] ^= 1
    decode([bytes(bad), s[1]])
    tests.append(('corrupt-reject', False))
except ValueError:
    tests.append(('corrupt-reject', True))
try:
    decode([s[0], s500[0]])
    tests.append(('mixed-reject', False))
except ValueError:
    tests.append(('mixed-reject', True))
tests.append(('arabic-70->1', text_segments('م' * 70) == 1))
tests.append(('arabic-71->2', text_segments('م' * 71) == 2))

json.dump({'capsule_hex': cap171.hex(), 'msgid': 9,
           'segments_hex': [x.hex() for x in s], 'port': PORT},
          open('sms_golden.json', 'w'), indent=1)

fails = 0
for name, ok in tests:
    print(('PASS' if ok else 'FAIL'), name)
    fails += not ok
print(f'cost: whisper msg = {len(s)} SMS; arabic text 200ch = {text_segments("م" * 200)} SMS')
print('SMS CODEC:', 'ALL PASS' if not fails else 'FAIL')
raise SystemExit(1 if fails else 0)
