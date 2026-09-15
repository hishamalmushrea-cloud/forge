#!/usr/bin/env python3
"""Missed-call ring protocol: free ~1-bit signaling with pre-agreed meanings."""
import json

MEANINGS = {1: 'تمام ✓', 2: 'اتصل بي ضروري', 3: 'تعال/خطر'}
WINDOW = 90.0


def dial_howto(n):
    return f'اتصل واقطع بعد رنة واحدة × {n} (فاصل ~10 ثوانٍ بينها)'


def decode(times):
    """Split ring timestamps (sec) into windowed events -> [(count, meaning)]."""
    ev, cur, start = [], [], None
    for t in sorted(times):
        if start is None or t - start > WINDOW:
            if cur:
                ev.append(cur)
            cur, start = [t], t
        else:
            cur.append(t)
    if cur:
        ev.append(cur)
    return [(len(e), MEANINGS.get(len(e), 'نمط غير معروف')) for e in ev]


tests = [
    ('single', decode([0.0]) == [(1, 'تمام ✓')]),
    ('double', decode([0.0, 15.0]) == [(2, 'اتصل بي ضروري')]),
    ('triple', decode([0.0, 10.0, 20.0]) == [(3, 'تعال/خطر')]),
    ('split-windows', decode([0.0, 100.0]) == [(1, 'تمام ✓'), (1, 'تمام ✓')]),
    ('empty', decode([]) == []),
    ('unknown-5', decode([0, 1, 2, 3, 4])[0][1] == 'نمط غير معروف'),
]
fails = 0
for name, ok in tests:
    print(('PASS' if ok else 'FAIL'), name)
    fails += not ok
print('howto(2):', dial_howto(2))
print('limits: needs visible CLI + call-state permission; carriers may delay; ~2 bits/min')
json.dump({'meanings': MEANINGS, 'window': WINDOW}, open('ring_map.json', 'w'), ensure_ascii=False)
print('RING CODE:', 'ALL PASS' if not fails else 'FAIL')
raise SystemExit(1 if fails else 0)
