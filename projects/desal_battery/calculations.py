#!/usr/bin/env python3
"""MUSHREA FORGE — Desalination battery model v2 (LEVEL 2, stdlib only).

PHYSICS: 1 mol e- removes 1 mol NaCl. Q = n*F/eta_F.
  E_net = Q * DNET_V  with DNET_V = 0.07V CALIBRATED to Pasta 2012 measured
  0.29 Wh/L @ 25% removal (0.29*3600/15210C = 0.069V). V1's 0.4V gap was 6x pessimistic.
  Capacities: Ag 248 mAh/g (TEXTBOOK); PB 100 mAh/g (SOURCE VERIFIED practical range 100-160).
STATUS: CALCULATED + CALIBRATED to a measured literature point.
"""
import json

F = 96485.0
C_SEA = 35.0
M_NACL = 58.44
V_CHG = 0.5           # V operating (ASSUMED; absolute value for power sizing)
DNET_V = 0.07         # V net gap (CALIBRATED to Pasta 0.29 Wh/L @25%)
ETA_F = 0.95          # (ASSUMED)
CAP_AG = 0.248        # Ah/g (TEXTBOOK)
CAP_PB = 0.100        # Ah/g (SOURCE VERIFIED conservative: lit. 100-160)
RO_REF = 3.5
THERMO_MIN = 1.0

def pass_energy(removal_frac, volume_L=1.0):
    mol = C_SEA * volume_L / M_NACL * removal_frac
    q_C = mol * F / ETA_F
    e_chg = q_C * V_CHG / 3600
    e_net = q_C * DNET_V / 3600
    return {"Q_Ah": round(q_C / 3600, 3), "E_chg_Wh": round(e_chg, 2),
            "E_rec_Wh": round(e_chg - e_net, 2), "E_net_Wh": round(e_net, 3)}

sweep = []
for r in (0.25, 0.5, 0.7, 0.8, 0.9, 0.95):
    e = pass_energy(r)
    sweep.append({"removal": r, "ppm_out": round(C_SEA * 1000 * (1 - r)),
                  "kWh_per_m3": e["E_net_Wh"], **e})
ppm, passes, e_tot = C_SEA * 1000, 0, 0.0
e90 = pass_energy(0.9)
while ppm >= 1000:
    ppm *= 0.1
    passes += 1
    e_tot += e90["E_net_Wh"]
q90 = e90["Q_Ah"]
res = {"params": {"V_chg": V_CHG, "DNET_V_calibrated": DNET_V, "eta_F": ETA_F,
                  "cap_Ag_Ah_g": CAP_AG, "cap_PB_Ah_g": CAP_PB},
       "calibration_anchor": {"removal": 0.25, "measured_Wh_per_L": 0.29,
                              "model_Wh_per_L": pass_energy(0.25)["E_net_Wh"]},
       "sweep": sweep,
       "cascade_90pct": {"passes": passes, "ppm_final": round(ppm, 1),
                         "E_net_Wh_per_L": round(e_tot, 2), "kWh_per_m3": round(e_tot, 2)},
       "electrode_g_per_L_cycle": {"Ag": round(q90 / CAP_AG, 1), "PB": round(q90 / CAP_PB, 1)},
       "current_A_8h": round(q90 / 8, 2)}
with open("results.json", "w") as f:
    json.dump(res, f, indent=1)

W, H, PL, PB, PT, PR = 660, 360, 64, 46, 30, 16
X = lambda r: PL + (r - 0.25) / (0.95 - 0.25) * (W - PL - PR)
Y = lambda e: (H - PB) - e / 4.0 * (H - PB - PT)
s = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" font-family="sans-serif">' % (W, H),
     '<rect width="%d" height="%d" fill="white"/>' % (W, H),
     '<text x="%d" y="18" text-anchor="middle" font-size="13" font-weight="bold">Desal battery: net energy vs removal (CALIBRATED to Pasta 2012)</text>' % (W // 2)]
for gv in (0, 1, 2, 3, 4):
    s.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="#e5e7eb"/>' % (PL, Y(gv), W - PR, Y(gv)))
    s.append('<text x="%s" y="%s" text-anchor="end" font-size="10">%s</text>' % (PL - 6, Y(gv) + 4, gv))
for p in sweep:
    s.append('<text x="%s" y="%s" text-anchor="middle" font-size="10">%d%%</text>' % (X(p["removal"]), H - PB + 16, p["removal"] * 100))
s.append('<text x="%d" y="%d" text-anchor="middle" font-size="11">salt removal per pass</text>' % (W // 2, H - 6))
s.append('<text x="14" y="%d" font-size="11" transform="rotate(-90 14 %d)" text-anchor="middle">kWh/m3 net</text>' % (H // 2, H // 2))
for ref, col, lab in ((THERMO_MIN, "#16a34a", "thermo min ~1"), (RO_REF, "#b45309", "RO ~3.5")):
    s.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-dasharray="5,4"/>' % (PL, Y(ref), W - PR, Y(ref), col))
    s.append('<text x="%s" y="%s" text-anchor="end" font-size="10" fill="%s">%s</text>' % (W - PR - 4, Y(ref) - 5, col, lab))
s.append('<polyline points="%s" fill="none" stroke="#2563eb" stroke-width="2.5"/>' %
         " ".join("%s,%s" % (X(p["removal"]), Y(p["kWh_per_m3"])) for p in sweep))
for p in sweep:
    s.append('<circle cx="%s" cy="%s" r="4" fill="#2563eb"/>' % (X(p["removal"]), Y(p["kWh_per_m3"])))
ax, ay = X(0.25), Y(0.29)
s.append('<circle cx="%s" cy="%s" r="6" fill="none" stroke="#dc2626" stroke-width="2"/>' % (ax, ay))
s.append('<text x="%s" y="%s" font-size="10" fill="#dc2626">Pasta measured 0.29</text>' % (ax + 10, ay - 8))
s.append('</svg>')
with open("chart.svg", "w") as f:
    f.write("\n".join(s))

print("anchor 25%%: model=%.3f Wh/L vs measured 0.29" % res["calibration_anchor"]["model_Wh_per_L"])
print("sweep:", [(p["removal"], p["kWh_per_m3"]) for p in sweep])
print("cascade: %d passes -> %.0fppm at %.2f kWh/m3" % (passes, ppm, e_tot))
print("electrodes/L-cycle: Ag=%.1fg PB=%.1fg | I(8h)=%.2fA" % (q90 / CAP_AG, q90 / CAP_PB, q90 / 8))
print("wrote results.json + chart.svg [CALCULATED+CALIBRATED]")
