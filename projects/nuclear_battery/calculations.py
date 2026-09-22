#!/usr/bin/env python3
"""MUSHREA FORGE — Nuclear battery analytical model (LEVEL 1/2, stdlib only).

MODEL: exponential decay P(t) = P0 * 2^(-t / t_half); P_elec = P_thermal * eta.
Lifetime electrical energy = integral of P_elec(t) dt = P_elec0 / lambda, lambda = ln2 / t_half.
INPUTS: public data (IEEE Spectrum isotope table; MMRTG flight data). See final_report SOURCES.
LIMITATIONS: ignores converter radiation damage, self-absorption, thermal scale losses.
STATUS of outputs: CALCULATED from SOURCE VERIFIED inputs + ASSUMED efficiencies.
"""
import json
import math

LN2 = math.log(2)
SEC_PER_YEAR = 365.25 * 24 * 3600

ISOTOPES = {
    "Ni-63":  {"half_life_y": 100.0, "spec_W_per_g": 0.0058, "eta": 0.05, "kind": "betavoltaic"},
    "H-3":    {"half_life_y": 12.3,  "spec_W_per_g": 0.33,   "eta": 0.05, "kind": "betavoltaic"},
    "Pu-238": {"half_life_y": 87.7,  "spec_W_per_g": 0.56,   "eta": 0.06, "kind": "RTG"},
}
P_ELEC0_W = 100e-6  # R1: 100 uW BOL (ASSUMED)
YEARS = 50

results = {"target_P_elec_uW": P_ELEC0_W * 1e6, "years": YEARS, "options": {}}
for name, iso in ISOTOPES.items():
    thalf = iso["half_life_y"]
    p_th0 = P_ELEC0_W / iso["eta"]
    mass_g = p_th0 / iso["spec_W_per_g"]
    lam_per_y = LN2 / thalf
    # lifetime electrical energy in Wh: E = P0 / lambda
    e_life_J = P_ELEC0_W / (lam_per_y / SEC_PER_YEAR)
    e_life_Wh = e_life_J / 3600.0
    traj = []
    for t in range(YEARS + 1):
        p = P_ELEC0_W * (2.0 ** (-t / thalf))
        traj.append(round(p * 1e6, 3))  # uW
    results["options"][name] = {
        "kind": iso["kind"],
        "half_life_y": thalf,
        "eta_assumed": iso["eta"],
        "P_thermal0_mW": round(p_th0 * 1000, 4),
        "isotope_mass_g": round(mass_g, 5),
        "lifetime_electric_Wh": round(e_life_Wh, 2),
        "P_uW_year20": traj[20],
        "trajectory_uW": traj,
    }

with open("results.json", "w") as f:
    json.dump(results, f, indent=1)

# ---- SVG chart (hand-drawn, no libs) ----
W, H, PL, PB, PT, PR = 640, 360, 64, 44, 24, 16
colors = {"Ni-63": "#2563eb", "H-3": "#dc2626", "Pu-238": "#16a34a"}
xs = list(range(YEARS + 1))
ymax = 100.0
X = lambda t: PL + t / YEARS * (W - PL - PR)
Y = lambda p: (H - PB) - p / ymax * (H - PB - PT)
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif">',
       f'<rect width="{W}" height="{H}" fill="white"/>',
       f'<text x="{W//2}" y="16" text-anchor="middle" font-size="13" font-weight="bold">Nuclear battery options @ 100 uW BOL — power vs time (CALCULATED)</text>']
for gv in (0, 25, 50, 75, 100):
    svg.append(f'<line x1="{PL}" y1="{Y(gv)}" x2="{W-PR}" y2="{Y(gv)}" stroke="#e5e7eb"/>')
    svg.append(f'<text x="{PL-6}" y="{Y(gv)+4}" text-anchor="end" font-size="10">{gv}</text>')
for t in range(0, YEARS + 1, 10):
    svg.append(f'<text x="{X(t)}" y="{H-PB+16}" text-anchor="middle" font-size="10">{t}y</text>')
svg.append(f'<text x="14" y="{H//2}" font-size="11" transform="rotate(-90 14 {H//2})" text-anchor="middle">uW electric</text>')
for name, iso in ISOTOPES.items():
    pts = " ".join(f"{X(t):.1f},{Y(results['options'][name]['trajectory_uW'][t]):.1f}" for t in xs)
    svg.append(f'<polyline points="{pts}" fill="none" stroke="{colors[name]}" stroke-width="2"/>')
lx = 90
for name in ISOTOPES:
    svg.append(f'<rect x="{lx}" y="{H-18}" width="26" height="10" fill="{colors[name]}"/>')
    svg.append(f'<text x="{lx+30}" y="{H-9}" font-size="11">{name}</text>')
    lx += 130
svg.append("</svg>")
with open("chart.svg", "w") as f:
    f.write("\n".join(svg))

# ---- console ----
print("TARGET: 100 uW electric BOL | eta beta=5% (ASSUMED), RTG=6% (SOURCE VERIFIED)")
for name, o in results["options"].items():
    print(f"{name:7s} [{o['kind']:12s}] mass={o['isotope_mass_g']} g | Pth0={o['P_thermal0_mW']} mW | "
          f"20y={o['P_uW_year20']} uW | lifetime={o['lifetime_electric_Wh']} Wh")
print("wrote results.json + chart.svg  [CALCULATED]")
