#!/usr/bin/env python3
"""MUSHREA FORGE — Alkaline electrolyzer Faraday model (LEVEL 2, stdlib only).

PHYSICS (textbook): Q = I*t; mol e- = Q/F; mol H2 = mol e-/2; V = n * Vm.
  F = 96485 C/mol; Vm = 24.45 L/mol at 25C/1atm (ideal gas).
  E_cell operating 1.8-2.2V (ASSUMED typical alkaline, verified by literature search);
  reversible 1.23V; H2 LHV = 33.33 kWh/kg, rho = 0.0837 kg/m3 -> 2.79 Wh/L.
STATUS: CALCULATED from textbook constants + ASSUMED operating voltage.
"""
import json

F = 96485.0          # C/mol (TEXTBOOK)
VM = 24.45           # L/mol (IDEAL GAS @25C)
E_OP = 2.0           # V operating (ASSUMED mid-range)
E_REV = 1.23         # V reversible (TEXTBOOK)
LHV_WH_PER_L = 2.79  # Wh/L H2 (TEXTBOOK derived)
TARGET_LPH = 1.5     # R1

def h2_lph(current_A):
    mol_per_h = current_A * 3600.0 / (2.0 * F)
    return mol_per_h * VM

rows, op = [], None
for i in [1, 2, 3, 4, 5, 6, 8, 10]:
    lph = h2_lph(i)
    pwr = E_OP * i
    wh_per_l = pwr / lph
    eff = LHV_WH_PER_L / wh_per_l
    ok = lph >= TARGET_LPH
    rows.append({"I_A": i, "H2_L_per_h": round(lph, 2), "O2_L_per_h": round(lph / 2, 2),
                 "P_W": round(pwr, 1), "Wh_per_L_H2": round(wh_per_l, 2),
                 "LHV_eff": round(eff, 3), "meets_R1": ok})
    if ok and op is None:
        op = rows[-1]

results = {"F": F, "Vm_L_per_mol": VM, "E_op_assumed_V": E_OP,
           "selected_point": op, "voltage_eff_1.23/2.0": round(E_REV / E_OP, 3),
           "curve": rows}
with open("results.json", "w") as f:
    json.dump(results, f, indent=1)

# ---- SVG chart: H2 L/h and power vs current ----
W, H, PL, PB, PT, PR = 660, 380, 60, 46, 30, 60
X = lambda i: PL + (i - 1) / 9 * (W - PL - PR)
Y = lambda v: (H - PB) - v / 5.0 * (H - PB - PT)
YP = lambda p: (H - PB) - p / 22.0 * (H - PB - PT)
s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif">',
     f'<rect width="{W}" height="{H}" fill="white"/>',
     f'<text x="{W//2}" y="18" text-anchor="middle" font-size="13" font-weight="bold">Electrolyzer: H2 rate &amp; power vs current @2.0V (CALCULATED)</text>']
for gv in (0, 1, 2, 3, 4, 5):
    s.append(f'<line x1="{PL}" y1="{Y(gv)}" x2="{W-PR}" y2="{Y(gv)}" stroke="#e5e7eb"/>')
    s.append(f'<text x="{PL-6}" y="{Y(gv)+4}" text-anchor="end" font-size="10">{gv} L/h</text>')
for pv in (0, 5, 10, 15, 20):
    s.append(f'<text x="{W-PR+4}" y="{YP(pv)+4}" font-size="10" fill="#b45309">{pv}W</text>')
for i in (1, 2, 4, 6, 8, 10):
    s.append(f'<text x="{X(i)}" y="{H-PB+16}" text-anchor="middle" font-size="10">{i}A</text>')
s.append(f'<line x1="{PL}" y1="{Y(TARGET_LPH)}" x2="{W-PR}" y2="{Y(TARGET_LPH)}" stroke="#dc2626" stroke-dasharray="5,4"/>')
s.append(f'<text x="{W-PR-4}" y="{Y(TARGET_LPH)-5}" text-anchor="end" font-size="10" fill="#dc2626">R1 = 1.5 L/h</text>')
s.append('<polyline points="' + " ".join(f"{X(r['I_A']):.1f},{Y(r['H2_L_per_h']):.1f}" for r in rows) +
       '" fill="none" stroke="#2563eb" stroke-width="2"/>')
s.append('<polyline points="' + " ".join(f"{X(r['I_A']):.1f},{YP(r['P_W']):.1f}" for r in rows) +
       '" fill="none" stroke="#b45309" stroke-width="2" stroke-dasharray="3,3"/>')
s.append(f'<rect x="90" y="{H-20}" width="26" height="10" fill="#2563eb"/><text x="120" y="{H-11}" font-size="11">H2 L/h</text>')
s.append(f'<rect x="220" y="{H-20}" width="26" height="10" fill="#b45309"/><text x="250" y="{H-11}" font-size="11">power W (right)</text>')
s.append("</svg>")
with open("chart.svg", "w") as f:
    f.write("\n".join(s))

print(f"SELECTED: {op['I_A']}A -> H2={op['H2_L_per_h']} L/h, O2={op['O2_L_per_h']} L/h, P={op['P_W']}W, {op['Wh_per_L_H2']} Wh/L, LHV eff={op['LHV_eff']}")
print(f"Voltage eff = 1.23/2.0 = {results['voltage_eff_1.23/2.0']}")
print("wrote results.json + chart.svg [CALCULATED]")
