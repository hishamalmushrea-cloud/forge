#!/usr/bin/env python3
"""MUSHREA FORGE — TEG demonstrator model (LEVEL 2, stdlib only).

ELECTRICAL: piecewise-linear interpolation of vendor-measured SP1848 table
  (SOURCE VERIFIED, 2 vendors agree): (dT, Voc, Isc). N modules in series.
  R_int = Voc/Isc per module; Pmax = (N*Voc)^2 / (4*N*R_int).
THERMAL: Q_through = P_elec/eta_te; eta_te=4% (ASSUMED textbook 3-5%);
  Q_loss=20% (ASSUMED); heatsink Tcold = Tamb + Q_rej*Rth.
  Tamb=35C (ASSUMED Taiz hot climate); Thot limit 140C (margin under 150C max).
STATUS: CALCULATED from SOURCE VERIFIED electrical table + ASSUMED thermal params.
"""
import json

# Vendor table: dT(C) -> (Voc V, Isc A) per SP1848-27145 module
TABLE = {20: (0.97, 0.225), 40: (1.80, 0.368), 60: (2.40, 0.469),
         80: (3.60, 0.558), 100: (4.80, 0.669)}
N = 2            # modules in series (SELECTED to meet R1)
ETA_TE = 0.04    # TEG conversion efficiency (ASSUMED)
Q_LOSS = 0.20    # extra heat loss fraction (ASSUMED)
T_AMB = 35.0     # hot-climate ambient (ASSUMED)
RTH = 0.5        # heatsink+fan K/W (REQUIRED, fan CPU-cooler class)
T_HOT_MAX = 140.0

def lerp(table, dt):
    ds = sorted(table)
    if dt <= ds[0]:
        v0, i0 = table[ds[0]]
        return v0 * dt / ds[0], i0 * dt / ds[0]
    for a, b in zip(ds, ds[1:]):
        if dt <= b:
            f = (dt - a) / (b - a)
            va, ia = table[a]; vb, ib = table[b]
            return va + f * (vb - va), ia + f * (ib - ia)
    vb, ib = table[ds[-1]]
    return vb, ib

rows, op_point = [], None
for dt in range(10, 105, 5):
    voc1, isc1 = lerp(TABLE, dt)
    r1 = voc1 / isc1
    voc_sys = N * voc1
    r_sys = N * r1
    pmax = voc_sys ** 2 / (4 * r_sys)
    q_rej = pmax / ETA_TE * (1 + Q_LOSS)
    t_cold = T_AMB + q_rej * RTH
    t_hot = t_cold + dt
    ok = (pmax >= 1.0) and (t_hot <= T_HOT_MAX)
    rows.append({"dT": dt, "Voc_sys_V": round(voc_sys, 2), "R_sys_ohm": round(r_sys, 2),
                 "Pmax_W": round(pmax, 3), "Q_heater_W": round(q_rej, 1),
                 "Tcold_C": round(t_cold, 1), "Thot_C": round(t_hot, 1), "meets_R1_safe": ok})
    if ok and op_point is None:
        op_point = rows[-1]

# Heater sizing at selected operating point dT=80 (nearest robust point)
sel = next(r for r in rows if r["dT"] == 80)
heater_rec_W = round(sel["Q_heater_W"] * 1.5, 0)  # 50% control margin

results = {"modules_series": N, "eta_te_assumed": ETA_TE, "Rth_selected": RTH,
           "Tamb_assumed": T_AMB, "first_feasible_point": op_point,
           "selected_point_dT80": sel, "heater_recommended_W": heater_rec_W,
           "matched_load_ohm": sel["R_sys_ohm"], "curve": rows}
with open("results.json", "w") as f:
    json.dump(results, f, indent=1)

# ---- SVG: Pmax(dT) N=1,2 + heater Q + 1W line ----
W, H, PL, PB, PT, PR = 660, 380, 60, 46, 30, 60
X = lambda dt: PL + (dt - 10) / 95 * (W - PL - PR)
Y = lambda p: (H - PB) - p / 2.0 * (H - PB - PT)
YQ = lambda q: (H - PB) - q / 60.0 * (H - PB - PT)
s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif">',
     f'<rect width="{W}" height="{H}" fill="white"/>',
     f'<text x="{W//2}" y="18" text-anchor="middle" font-size="13" font-weight="bold">TEG system: SP1848 x{N} series — power &amp; heat vs dT (CALCULATED)</text>']
for gv in (0, 0.5, 1.0, 1.5, 2.0):
    s.append(f'<line x1="{PL}" y1="{Y(gv)}" x2="{W-PR}" y2="{Y(gv)}" stroke="#e5e7eb"/>')
    s.append(f'<text x="{PL-6}" y="{Y(gv)+4}" text-anchor="end" font-size="10">{gv}W</text>')
for qv in (0, 20, 40, 60):
    s.append(f'<text x="{W-PR+4}" y="{YQ(qv)+4}" font-size="10" fill="#b45309">{qv}W</text>')
for dt in range(10, 105, 10):
    s.append(f'<text x="{X(dt)}" y="{H-PB+16}" text-anchor="middle" font-size="10">{dt}</text>')
s.append(f'<text x="{W//2}" y="{H-6}" text-anchor="middle" font-size="11">dT (K)</text>')
s.append(f'<line x1="{PL}" y1="{Y(1.0)}" x2="{W-PR}" y2="{Y(1.0)}" stroke="#dc2626" stroke-dasharray="5,4"/>')
s.append(f'<text x="{W-PR-4}" y="{Y(1.0)-5}" text-anchor="end" font-size="10" fill="#dc2626">R1 = 1W</text>')
for n, col in ((1, "#93c5fd"), (N, "#2563eb")):
    pts = []
    for r in rows:
        voc1 = r["Voc_sys_V"] / N
        r1 = r["R_sys_ohm"] / N
        p = (n * voc1) ** 2 / (4 * n * r1)
        pts.append(f"{X(r['dT']):.1f},{Y(p):.1f}")
    s.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{col}" stroke-width="2"/>')
pts = " ".join(f"{X(r['dT']):.1f},{YQ(r['Q_heater_W']):.1f}" for r in rows)
s.append(f'<polyline points="{pts}" fill="none" stroke="#b45309" stroke-width="2" stroke-dasharray="3,3"/>')
s.append(f'<rect x="80" y="{H-20}" width="26" height="10" fill="#93c5fd"/><text x="110" y="{H-11}" font-size="11">Pmax 1 module</text>')
s.append(f'<rect x="230" y="{H-20}" width="26" height="10" fill="#2563eb"/><text x="260" y="{H-11}" font-size="11">Pmax 2 series</text>')
s.append(f'<rect x="380" y="{H-20}" width="26" height="10" fill="#b45309"/><text x="410" y="{H-11}" font-size="11">heater Q (right axis)</text>')
s.append("</svg>")
with open("chart.svg", "w") as f:
    f.write("\n".join(s))

print(f"First feasible (P>=1W, Thot<={T_HOT_MAX}C): dT={op_point['dT']} P={op_point['Pmax_W']}W Thot={op_point['Thot_C']}C")
print(f"SELECTED dT=80: Voc={sel['Voc_sys_V']}V R={sel['R_sys_ohm']}ohm P={sel['Pmax_W']}W Q={sel['Q_heater_W']}W Thot={sel['Thot_C']}C Tcold={sel['Tcold_C']}C")
print(f"Heater recommended: {heater_rec_W}W @12V | Matched load: {sel['R_sys_ohm']} ohm")
print("wrote results.json + chart.svg [CALCULATED]")
