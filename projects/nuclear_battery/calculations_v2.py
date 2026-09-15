#!/usr/bin/env python3
"""MUSHREA FORGE — Nuclear battery model v0.2 (LEVEL 2, stdlib only).

UPGRADES over v0.1 (closing the review gaps):
1. SELF-ABSORPTION: only fraction ETA_SELF of decays escape a real foil (ESTIMATED 0.5 parametric).
2. CONVERTER DEGRADATION: P(t) *= (1-DELTA)^t, DELTA=0.5%/yr (ESTIMATED, radiation damage + aging).
3. RTG MICROSCALE PROOF: bulk thermoelectrics need Q = G_te*dT heat flow; mg-scale source cannot
   supply it -> quantitative infeasibility (no hand-waving).
STATUS: CALCULATED from SOURCE VERIFIED v0.1 inputs + ESTIMATED v0.2 factors (labeled).
"""
import json

LN2 = 0.69314718056
SEC_Y = 365.25 * 24 * 3600
ISO = {
    "Ni-63":  {"hl": 100.0, "sp": 0.0058, "eta": 0.05, "kind": "beta"},
    "H-3":    {"hl": 12.3,  "sp": 0.33,   "eta": 0.05, "kind": "beta"},
    "Pu-238": {"hl": 87.7,  "sp": 0.56,   "eta": 0.06, "kind": "rtg"},
}
ETA_SELF = 0.5   # ESTIMATED parametric (beta only)
DELTA = 0.005    # ESTIMATED converter degradation per year
P0 = 100e-6      # 100 uW BOL target
YEARS = 50

out = {"v02_factors": {"ETA_SELF_beta": ETA_SELF, "DELTA_per_yr": DELTA}, "options": {}}
for name, iso in ISO.items():
    eff = iso["eta"] * (ETA_SELF if iso["kind"] == "beta" else 1.0)
    mass = (P0 / eff) / iso["sp"]
    traj = [P0 * (2.0 ** (-t / iso["hl"])) * ((1 - DELTA) ** t) * 1e6 for t in range(YEARS + 1)]
    e_J = sum(P0 * (2.0 ** (-(t + 0.5) / iso["hl"])) * ((1 - DELTA) ** (t + 0.5)) * SEC_Y for t in range(400))
    out["options"][name] = {"mass_g_v02": round(mass, 5), "P_uW_20y_v02": round(traj[20], 2),
                             "lifetime_Wh_v02": round(e_J / 3600, 2), "trajectory_uW": [round(v, 3) for v in traj]}

# ---- RTG microscale proof (Pu-238 @100uW: Pth = 1.667 mW) ----
Pth = P0 / ISO["Pu-238"]["eta"]
DT_NEED = 80.0
G_bulk = [0.1, 0.5, 1.0]  # W/K, cm-scale TE module range (ESTIMATED)
proof = {"Pth_mW": round(Pth * 1000, 4),
         "dT_achievable_K": {str(g): round(Pth / g, 4) for g in G_bulk},
         "G_required_uW_per_K": round(Pth / DT_NEED * 1e6, 2),
         "shortfall_factor": {str(g): round(g / (Pth / DT_NEED)) for g in G_bulk},
         "verdict": "INFEASIBLE at bulk scale: achievable dT milli-Kelvin vs 80K needed; "
                    "requires G~21 uW/K (MEMS/nanoscale research domain, not buildable here)"}
out["rtg_microscale_proof"] = proof
with open("results_v2.json", "w") as f:
    json.dump(out, f, indent=1)

# ---- SVG: Ni-63 v0.1 vs v0.2 + H-3 v0.2 ----
v1 = json.load(open("results.json"))
W, H, PL, PB, PT, PR = 660, 380, 60, 46, 30, 16
X = lambda t: PL + t / YEARS * (W - PL - PR)
Y = lambda p: (H - PB) - p / 100.0 * (H - PB - PT)
s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif">',
     f'<rect width="{W}" height="{H}" fill="white"/>',
     f'<text x="{W//2}" y="18" text-anchor="middle" font-size="13" font-weight="bold">Ni-63/H-3: v0.1 ideal vs v0.2 realistic (CALCULATED)</text>']
for gv in (0, 25, 50, 75, 100):
    s.append(f'<line x1="{PL}" y1="{Y(gv)}" x2="{W-PR}" y2="{Y(gv)}" stroke="#e5e7eb"/>')
    s.append(f'<text x="{PL-6}" y="{Y(gv)+4}" text-anchor="end" font-size="10">{gv}</text>')
for t in range(0, YEARS + 1, 10):
    s.append(f'<text x="{X(t)}" y="{H-PB+16}" text-anchor="middle" font-size="10">{t}y</text>')
series = [("Ni-63 v0.1", v1["options"]["Ni-63"]["trajectory_uW"], "#93c5fd"),
          ("Ni-63 v0.2", out["options"]["Ni-63"]["trajectory_uW"], "#2563eb"),
          ("H-3 v0.2", out["options"]["H-3"]["trajectory_uW"], "#dc2626")]
for name, tr, col in series:
    pts = " ".join(f"{X(t):.1f},{Y(v):.1f}" for t, v in enumerate(tr))
    s.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2"/>')
lx = 80
for name, _, col in series:
    s.append(f'<rect x="{lx}" y="{H-18}" width="26" height="10" fill="{col}"/>')
    s.append(f'<text x="{lx+30}" y="{H-9}" font-size="11">{name}</text>')
    lx += 150
s.append("</svg>")
with open("chart_v2.svg", "w") as f:
    f.write("\n".join(s))

for n, o in out["options"].items():
    print(f"{n}: mass_v02={o['mass_g_v02']}g 20y={o['P_uW_20y_v02']}uW life={o['lifetime_Wh_v02']}Wh")
print(f"RTG proof: Pth={proof['Pth_mW']}mW dT_ach={proof['dT_achievable_K']} G_req={proof['G_required_uW_per_K']}uW/K shortfall={proof['shortfall_factor']}")
print("wrote results_v2.json + chart_v2.svg [CALCULATED]")
