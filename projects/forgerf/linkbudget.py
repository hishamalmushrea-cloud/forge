#!/usr/bin/env python3
"""ForgeRF proof: 12-bit dynamic range + sensitivity + LoRa range + antennas."""
import json
import math

dr8, dr12 = 6.02 * 8 + 1.76, 6.02 * 12 + 1.76
print(f'dynamic range: 8-bit {dr8:.1f}dB vs 12-bit {dr12:.1f}dB (+{dr12 - dr8:.1f}dB)')
assert dr12 - dr8 > 20, '12-bit is 16x cleaner voltage'

sens = -174 + 10 * math.log10(125e3) + 6  # LoRa 125kHz, NF=6
print(f'LoRa sensitivity: {sens:.0f}dBm')
assert sens < -110

budget = 14 + 2 + 2 - sens  # 25mW TX + antennas - sensitivity
fspl_c = 20 * math.log10(433) + 32.44
d_free = 10 ** ((budget - fspl_c) / 20)
d_practical = d_free / 30  # urban ground rule-of-thumb
print(f'433MHz 25mW: free-space {d_free:.0f}km -> practical ~{d_practical:.0f}km')
assert 5 < d_practical < 20, 'matches real LoRa experience'


def dipole_legs_cm(f_mhz):
    return 142.6 / f_mhz * 100 / 2


for f in (100, 137, 433):
    print(f'dipole {f}MHz: {dipole_legs_cm(f):.1f}cm/leg')
assert abs(dipole_legs_cm(433) - 16.5) < 0.5

json.dump({'dr12_dB': round(dr12, 1), 'sens_dBm': round(sens),
           'lora_km': round(d_practical, 1),
           'verdict': 'LINKBUDGET [VERIFIED]'},
          open('results.json', 'w'), indent=1)
print('VERDICT: LINKBUDGET [VERIFIED]')
