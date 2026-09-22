#!/usr/bin/env python3
"""Betavoltaic truth model: Ni-63 decay, 50-year curve, 100uW budget, 1W math."""
import json

HL = 100.1  # Ni-63 half-life (years)
P0 = 100e-6  # BV100 claimed watts

p50 = 0.5 ** (50 / HL)
print(f'power at 50y: {p50:.1%} of day one')
assert 0.70 < p50 < 0.72, '50-year claim physics'

E_tot = P0 * 50 * 365 * 24
print(f'total lifetime energy: {E_tot:.1f}Wh (a phone holds ~15Wh, delivered in a day!)')
assert 43 < E_tot < 45

phone_factor = 0.25 / P0
print(f'smartphone needs {phone_factor:.0f}x the BV100')
assert phone_factor == 2500

# isotope economics (generous 10% conversion; Ni-63 ~5.7mW/g thermal, $4000/g in 2026)
m_g = P0 / (5.7e-3 * 0.10)
cost = m_g * 4000
print(f'Ni-63 per unit: ~{m_g:.2f}g -> isotope alone ~${cost:.0f}')
assert cost > 100, 'consumer-price mass production implausible'

units_1W = 1 / P0
print(f'1W version = {units_1W:.0f} stacked units -> ${cost * units_1W / 1e6:.1f}M isotope')
assert units_1W == 10000

DEVICES = [('ساعة RTC', 1e-6), ('حساس حرارة', 5e-6), ('منارة BLE نابضة + مكثف', 50e-6),
           ('شاشة حبر (تحديث نادر)', 10e-6), ('LED خافت مستمر', 1e-3),
           ('هاتف ذكي', 0.25), ('درون', 50.0)]
print('device budget:')
for name, w in DEVICES:
    print(f"  {'PASS' if w <= P0 else 'FAIL'} {name}: needs {w / P0:.1f}x")
assert sum(1 for _, w in DEVICES if w <= P0) == 4, 'only micropower loads pass'
print('temp claim -60..+120C: consistent with diamond bandgap (vendor claim, plausible)')

json.dump({'p50_pct': round(p50 * 100, 1), 'E_Wh': round(E_tot, 1),
           'phone_x': phone_factor, 'isotope_g': round(m_g, 3),
           'isotope_$': round(cost), 'units_1W': units_1W,
           'verdict': 'NUCELL [VERIFIED: real physics, micropower only]'},
          open('results.json', 'w'), indent=1)
print('VERDICT: NUCELL [VERIFIED]')
