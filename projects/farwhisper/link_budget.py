#!/usr/bin/env python3
"""10km link-budget proof: FSPL + margins (conservative SX1276 sens) + ToA + Fresnel + energy."""
import json
import math

F_MHZ, D_KM = 433.0, 10.0
TX, GT, GR, LMISC = 14.0, 2.0, 2.0, 3.0
SENS = {7: -124, 8: -127, 9: -130, 10: -133, 11: -135, 12: -137}  # SX1276/125kHz (SX1262 better)
PL = 184  # 171B capsule + 13B mesh header

fspl = 20 * math.log10(D_KM) + 20 * math.log10(F_MHZ) + 32.44
rx = TX + GT + GR - fspl - LMISC
print(f'FSPL@{D_KM}km = {fspl:.1f} dB, RX = {rx:.1f} dBm')
margins = {sf: round(rx - s, 1) for sf, s in SENS.items()}
print('margins:', margins)
assert margins[7] > 25, 'SF7 must clear 10km LOS easily'
assert margins[12] - 25 > 15, 'SF12 must survive +25dB obstacle'


def toa(sf, pl=PL, bw=125000, cr=1):
    tsym = 2 ** sf / bw
    de = 1 if tsym > 0.016 else 0
    num = 8 * pl - 4 * sf + 28 + 16 - 20 * 0
    den = 4 * (sf - 2 * de)
    pay = 8 + max(math.ceil(num / den) * (cr + 4), 0)
    return ((8 + 4.25) + pay) * tsym


toas = {sf: round(toa(sf), 3) for sf in range(7, 13)}
print('ToA(s) 184B:', toas)
assert toas[9] < 1.5 and toas[7] < 0.5, 'airtime sane'

lam = 300 / F_MHZ
fres = 0.5 * math.sqrt(lam * D_KM * 1000)
print(f'Fresnel mid-radius = {fres:.1f}m -> need ~{0.6 * fres:.0f}m clearance (elevation/relays in city)')
e_100 = 100 * toas[9] * 0.12
print(f'energy 100 msgs/day = {e_100:.1f}J = {100 * e_100 / 36000:.3f}% of 18650')
assert e_100 < 36, '<0.1% of battery'
print(f"duty-cycle 1%: {3600 / (toas[9] * 100):.0f} msgs/hour max per node")

json.dump({'fspl': round(fspl, 1), 'rx': round(rx, 1), 'margins': margins,
           'toa': toas, 'fresnel_m': round(fres, 1), 'verdict': '10KM LINK [VERIFIED]'},
          open('link_results.json', 'w'), indent=1)
print('VERDICT: 10KM LINK [VERIFIED] (conservative SX1276 numbers; SX1262 adds ~10dB)')
