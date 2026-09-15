#!/usr/bin/env python3
"""captures.csv -> measured table. --selftest validates analysis on synthetic data."""
import csv
import json
import sys

E_TX_MJ = 2.475


def analyze(rows):
    per = {}
    for r in rows:
        if not r:
            continue
        if r[0] == 'RESYNC':
            per.setdefault(r[1], {'ok': 0, 'n': 0, 'lat': [], 'rs': 0})['rs'] += 1
        elif r[0] == 'CAP':
            d = per.setdefault(r[1], {'ok': 0, 'n': 0, 'lat': [], 'rs': 0})
            d['n'] += 1
            if r[5] == '1':
                d['ok'] += 1
                d['lat'].append(int(r[6]))
    out = {}
    for k, d in per.items():
        pdr = d['ok'] / max(d['n'], 1)
        lat = sum(d['lat']) / max(len(d['lat']), 1)
        out[k] = {'pdr': round(pdr, 4), 'lat_slots': round(lat, 3),
                  'mJ_per_delivered': round((lat + 1) * E_TX_MJ, 3) if d['ok'] else None,
                  'resyncs': d['rs'], 'n': d['n']}
    return out


def selftest():
    rows = [['CAP', 'chaos', str(i), '5', '-70', '1', '0'] for i in range(100)]
    rows += [['CAP', 'fixed', str(i), '0', '-70', '1' if i % 2 else '0', '0'] for i in range(100)]
    rows.append(['RESYNC', 'chaos', '50'])
    m = analyze(rows)
    assert m['chaos']['pdr'] == 1.0 and m['fixed']['pdr'] == 0.5, m
    assert m['chaos']['resyncs'] == 1 and m['fixed']['resyncs'] == 0, m
    assert m['chaos']['mJ_per_delivered'] == round(E_TX_MJ, 3), m
    print('MEASURE SELFTEST PASS:', json.dumps(m))


def main():
    if '--selftest' in sys.argv:
        return selftest()
    rows = list(csv.reader(open(sys.argv[1] if len(sys.argv) > 1 else 'captures.csv')))
    m = analyze(rows)
    json.dump(m, open('measured.json', 'w'), indent=1)
    print('| Scheme | PDR | lat slots | mJ/delivered | resyncs | n |')
    for k, d in sorted(m.items()):
        print(f"| {k} | {d['pdr']} | {d['lat_slots']} | {d['mJ_per_delivered']} | {d['resyncs']} | {d['n']} |")


if __name__ == '__main__':
    main()
