#!/usr/bin/env python3
"""MUSHREA FORGE — Betavoltaic sensor node energy model (LEVEL 2, stdlib only).

BUDGET: harvested(t) = 100uW * 2^(-t/100) * 0.995^t * ETA_HARV  (v0.2 source numbers)
LOAD(tx_min) = E_BURST/(tx_min*60) + P_SLEEP + V*I_LEAK
EOL: first year harvested < load. BUFFER: 0.5*C*(Vhi^2-Vlo^2) must cover 3x E_BURST.
WEEK SIM: 60s-step capacitor integrator with TX events, 7 days, TX=30min.
STATUS: CALCULATED from v0.2 VERIFIED source + ASSUMED electronics (D3/D4).
"""
import json

P_BOL = 100e-6      # v0.2: 0.69 g Ni-63
HL = 100.0
ETA_HARV = 0.5      # ASSUMED
E_BURST = 50e-3     # J per measure+TX (ASSUMED w/ margin)
P_SLEEP = 2e-6      # W
I_LEAK = 2e-6       # A supercap leakage (ASSUMED; sensitivity below)
V_HI, V_LO, V_NOM = 3.3, 2.0, 3.0
C_FARAD = 0.1

def harvested(t_y):
    return P_BOL * (2.0 ** (-t_y / HL)) * (0.995 ** t_y) * ETA_HARV

def load_avg(tx_min, i_leak=I_LEAK):
    return E_BURST / (tx_min * 60) + P_SLEEP + V_NOM * i_leak

def eol_year(tx_min, i_leak=I_LEAK):
    need = load_avg(tx_min, i_leak)
    t = 0.0
    while t <= 150:
        if harvested(t) < need:
            return round(t, 1)
        t += 0.5
    return ">150"

# EOL vs TX interval + leakage sensitivity
intervals = [15, 20, 25, 30, 45, 60, 120]
eol_table = {tx: eol_year(tx) for tx in intervals}
leak_sens = {il: {tx: eol_year(tx, il) for tx in (20, 30, 60)} for il in (1e-6, 2e-6, 5e-6)}
# Buffer margin + recharge time at BOL
e_cap = 0.5 * C_FARAD * (V_HI ** 2 - V_LO ** 2)
margin = e_cap / E_BURST
t_recharge_min = E_BURST / (harvested(0) - P_SLEEP - V_NOM * I_LEAK) / 60

# Week simulation, TX=30min, dt=60s
dt, E = 60.0, e_cap
vmin, trace = 99, []
for step in range(7 * 24 * 60):
    t_y = step * dt / (365.25 * 24 * 3600)
    E = min(e_cap, E + (harvested(t_y) - P_SLEEP - V_NOM * I_LEAK) * dt)
    if step % 30 == 0 and step > 0:
        E -= E_BURST  # TX event (no TX if E insufficient -> counted)
    import math
    v = math.sqrt(max(0, 2 * E / C_FARAD))
    vmin = min(vmin, v)
    if step % 60 == 0:
        trace.append(round(v, 3))
week_ok = vmin >= V_LO

res = {"P_BOL_uW": P_BOL * 1e6, "ETA_HARV": ETA_HARV, "E_BURST_mJ": E_BURST * 1000,
       "C_F": C_FARAD, "buffer_margin_x": round(margin, 1),
       "recharge_min_BOL": round(t_recharge_min, 1),
       "EOL_years_vs_TXmin": eol_table, "leakage_sensitivity": leak_sens,
       "week_TX30_vmin": round(vmin, 3), "week_ok": week_ok, "week_trace_V": trace}
with open("results.json", "w") as f:
    json.dump(res, f, indent=1)

# ---- SVG 1: EOL vs TX interval ----
W, H, PL, PB, PT, PR = 660, 340, 60, 46, 30, 16
X = lambda tx: PL + (tx - 15) / (120 - 15) * (W - PL - PR)
Y = lambda e: (H - PB) - min(e, 150) / 150 * (H - PB - PT)
s = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" font-family="sans-serif">' % (W, H),
     '<rect width="%d" height="%d" fill="white"/>' % (W, H),
     '<text x="%d" y="18" text-anchor="middle" font-size="13" font-weight="bold">Node lifetime vs TX interval (CALCULATED, leak=2uA)</text>' % (W // 2)]
for gv in (0, 25, 50, 75, 100, 125, 150):
    s.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="#e5e7eb"/>' % (PL, Y(gv), W - PR, Y(gv)))
    s.append('<text x="%s" y="%s" text-anchor="end" font-size="10">%sy</text>' % (PL - 6, Y(gv) + 4, gv))
for tx in intervals:
    s.append('<text x="%s" y="%s" text-anchor="middle" font-size="10">%s</text>' % (X(tx), H - PB + 16, tx))
s.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="#dc2626" stroke-dasharray="5,4"/>' % (PL, Y(20), W - PR, Y(20)))
s.append('<text x="%s" y="%s" text-anchor="end" font-size="10" fill="#dc2626">R1 = 20y</text>' % (W - PR - 4, Y(20) - 5))
pts = " ".join("%s,%s" % (X(tx), Y(e if isinstance(e, float) else 150)) for tx, e in eol_table.items())
s.append('<polyline points="%s" fill="none" stroke="#2563eb" stroke-width="2.5"/>' % pts)
for tx, e in eol_table.items():
    ev = e if isinstance(e, float) else 150
    s.append('<circle cx="%s" cy="%s" r="4" fill="#2563eb"/>' % (X(tx), Y(ev)))
    s.append('<text x="%s" y="%s" text-anchor="middle" font-size="9">%s</text>' % (X(tx), Y(ev) - 8, e))
s.append('</svg>')
with open("chart_eol.svg", "w") as f:
    f.write("\n".join(s))

# ---- SVG 2: week Vcap trace ----
W2, H2 = 660, 260
X2 = lambda i: PL + i / (len(trace) - 1) * (W2 - PL - PR)
Y2 = lambda v: (H2 - PB) - (v - 1.5) / 2.0 * (H2 - PB - PT)
g = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" font-family="sans-serif">' % (W2, H2),
     '<rect width="%d" height="%d" fill="white"/>' % (W2, H2),
     '<text x="%d" y="18" text-anchor="middle" font-size="13" font-weight="bold">Supercap voltage over 7 days, TX/30min (SIMULATED)</text>' % (W2 // 2)]
for gv in (2.0, 2.5, 3.0, 3.3):
    g.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="#e5e7eb"/>' % (PL, Y2(gv), W2 - PR, Y2(gv)))
    g.append('<text x="%s" y="%s" text-anchor="end" font-size="10">%sV</text>' % (PL - 6, Y2(gv) + 4, gv))
g.append('<polyline points="%s" fill="none" stroke="#16a34a" stroke-width="1.5"/>' %
         " ".join("%s,%s" % (X2(i), Y2(v)) for i, v in enumerate(trace)))
for d in range(8):
    g.append('<text x="%s" y="%s" text-anchor="middle" font-size="10">d%d</text>' % (X2(d * 24), H2 - PB + 16, d))
g.append('</svg>')
with open("chart_week.svg", "w") as f:
    f.write("\n".join(g))

print("EOL(y) vs TX(min):", eol_table)
print("leak sens:", leak_sens)
print(f"buffer margin={margin:.1f}x recharge_BOL={t_recharge_min:.1f}min week_vmin={vmin:.2f}V ok={week_ok}")
print("wrote results.json + chart_eol.svg + chart_week.svg [CALCULATED/SIMULATED]")
