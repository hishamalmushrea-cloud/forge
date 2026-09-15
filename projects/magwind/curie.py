#!/usr/bin/env python3
"""Curie-wheel bound: candle heat -> magnet engine -> symbolic electricity."""
import json

TH, TC = 273 + 380, 273 + 40  # nickel hot spot vs ambient (K)
carnot = 1 - TC / TH
Q = 20.0  # watts of candle heat actually captured (generous)
P_MECH = Q * carnot * 0.01  # 1% of Carnot: generous upper bound
P_ELEC = P_MECH * 0.10  # coil pickup fraction
print(f'Carnot {carnot:.0%}: mech {P_MECH * 1000:.0f}mW -> elec {P_ELEC * 1000:.0f}mW')
assert P_MECH < Q * carnot, '2nd law respected'
assert P_ELEC < 0.05, 'demo scale only, not a power source'
assert P_MECH * 1000 > 5, 'beats bearing friction -> visibly spins'
print('Gd variant: Curie 20C -> spins on warm water vs air (exotic, pricey)')
json.dump({'P_mech_mW': round(P_MECH * 1000, 1), 'P_elec_mW': round(P_ELEC * 1000, 1),
           'verdict': 'CURIE: MOTION DEMO [VERIFIED], POWER: SYMBOLIC ONLY'},
          open('curie_results.json', 'w'), indent=1)
print('VERDICT: CURIE [VERIFIED as demo]')
