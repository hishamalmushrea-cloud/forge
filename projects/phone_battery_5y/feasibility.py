#!/usr/bin/env python3
"""MUSHREA FORGE — 5-year phone battery feasibility (LEVEL 1 analytical).

QUESTION: store 5 years of smartphone energy in a phone-sized battery, zero recharging.
METHOD: E_needed = E_day * 365 * 5; mass = E / density for each storage physics.
SOURCES: phone/battery densities from web research (see report); Ni-63 numbers from
  our v0.2 VERIFIED model (0.69g per 100uW @ ETA_SELF=0.5, eta=5%).
STATUS: CALCULATED. Verdict logic: INFEASIBLE if lightest option >> phone budget (~50g).
"""
E_DAY = 18.5  # Wh/day = one 5000mAh charge per day (SOURCE VERIFIED 18.5Wh)
YEARS = 5
E_NEED = E_DAY * 365 * YEARS
P_AVG = E_DAY / 24  # W continuous average

# name -> (Wh/kg, basis)
STORAGE = {
    "Li-ion (260 Wh/kg)": (260, "SOURCE VERIFIED"),
    "Li-SOCl2 primary (~300 Wh/kg)": (300, "ESTIMATED practical"),
    "Gasoline+20% engine (2400 Wh/kg fuel-only)": (2400, "TEXTBOOK, ignores hardware"),
    # Ni-63 electric over 5y per gram: 0.0058 W/g *0.05*0.5 * 43800 h
    "Ni-63 betavoltaic v0.2 (5y energy)": (0.0058 * 0.05 * 0.5 * 365 * 5 * 24 * 1000, "CALCULATED from v0.2"),  # x1000: Wh/g->Wh/kg
}
print(f"E_day={E_DAY}Wh  E_5y={E_NEED:,.0f}Wh  P_avg={P_AVG:.2f}W continuous")
print(f"{'storage':42s} {'mass for 5y':>12s}  basis")
for name, (dens, basis) in STORAGE.items():
    print(f"{name:42s} {E_NEED / dens:10,.1f} kg  [{basis}]")
# Ni-63 sanity via v0.2 mass route: 0.69g/100uW -> kg per watt
ni_kg_per_W = 0.69 / 100e-6 / 1000
print(f"\nNi-63 cross-check: {ni_kg_per_W:.1f} kg per watt continuous -> {ni_kg_per_W * P_AVG:.1f} kg for phone avg power")
# What density WOULD be needed in a 50 g phone battery?
need = E_NEED / 0.05
print(f"Required density in 50g battery: {need:,.0f} Wh/kg = {need / 260:.0f}x Li-ion")
print("Only nuclear-reaction densities reach this; no watt-scale licensable phone device exists.")
# Sensitivity on usage
print("\nSensitivity (mass Li-ion for 5y):")
for d in (5, 15, 30):
    print(f"  {d:2d} Wh/day -> {d * 365 * 5 / 260:,.1f} kg")
print("\nVERDICT: INFEASIBLE [CALCULATED]")
