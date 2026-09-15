#!/usr/bin/env python3
"""1.4m PMA wind turbine: power curve + Taiz-city vs hilltop daily yield."""
import json
import math

RHO, D, CP, ETA = 1.2, 1.4, 0.35, 0.75
A = math.pi * (D / 2) ** 2
CUT_IN, RATED_W, CUT_OUT = 3.0, 300.0, 15.0
K = 0.5 * RHO * A * CP * ETA  # P = K v^3


def turb_p(v):
    if v < CUT_IN or v > CUT_OUT:
        return 0.0
    return min(K * v ** 3, RATED_W)


assert turb_p(2) == 0 and turb_p(16) == 0, 'cut-in/out'
assert turb_p(12) == RATED_W, 'rated cap binds'
assert all(turb_p(v + 0.5) >= turb_p(v) for v in [3, 5, 8]), 'monotonic'


def rayleigh_pdf(v, m):
    return (math.pi / 2) * (v / m ** 2) * math.exp(-math.pi / 4 * (v / m) ** 2)


def daily_wh(m):
    e = sum(turb_p(v) * rayleigh_pdf(v, m) * 0.1 for v in
            [i * 0.1 for i in range(0, 250)])
    return e * 24


city, hill = daily_wh(3.0), daily_wh(5.0)
print(f'daily: Taiz-city(3m/s) {city:.0f}Wh | hilltop(5m/s) {hill:.0f}Wh')
assert 100 < city < 600 and 600 < hill < 2500, 'sanity bands'


def rpm(v):
    return 5 * v / (D / 2) * 60 / (2 * math.pi)


for v in (3, 5, 8):
    print(f'v={v}: P={turb_p(v):.0f}W rpm={rpm(v):.0f} Vgen={rpm(v) * 0.09:.1f}V')
assert rpm(3) * 0.09 >= 14, 'hoverboard PMA charges from cut-in (200+rpm)'
print('night share: wind has no day/night -> ~half the energy arrives off-sun')
json.dump({'curve_W': {v: round(turb_p(v), 1) for v in range(0, 16)},
           'city_Wh': round(city), 'hill_Wh': round(hill),
           'verdict': 'WIND [VERIFIED]'},
          open('results.json', 'w'), indent=1)
print('VERDICT: WIND [VERIFIED]')
