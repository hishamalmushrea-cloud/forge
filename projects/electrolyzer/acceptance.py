#!/usr/bin/env python3
"""MUSHREA FORGE — Acceptance checker for physical tests T2/T3/T4.
Usage: python3 acceptance.py run.csv H2_mL O2_mL
  run.csv : Arduino serial log (t_s,Vcell_V,ImA,coulombs,H2_pred_mL,relay)
  H2_mL/O2_mL : volumes measured by displacement (mL)
Checks: T2 Faraday volume within 15% | T3 O2:H2 ratio 1:2 within 10% | T4 current stable (std/mean<10%)
STATUS: EXECUTED on SIMULATED data (virtual commissioning); PENDING on real hardware data.
"""
import csv, math, sys

def mean(xs): return sum(xs) / len(xs)
def stdev(xs):
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))

def check(csv_path, h2_ml, o2_ml):
    rows = list(csv.DictReader(open(csv_path)))
    I = [float(r["ImA"]) / 1000.0 for r in rows]
    pred_ml = float(rows[-1]["H2_pred_mL"])
    dur_min = (float(rows[-1]["t_s"]) - float(rows[0]["t_s"])) / 60.0
    t2_err = abs(h2_ml - pred_ml) / pred_ml
    t2 = t2_err <= 0.15
    ratio = o2_ml / h2_ml if h2_ml > 0 else 0
    t3 = abs(ratio - 0.5) / 0.5 <= 0.10
    stab = stdev(I) / mean(I) if mean(I) else 1
    t4 = stab < 0.10
    print(f"samples={len(rows)} duration={dur_min:.1f}min I_mean={mean(I):.2f}A V_pred_H2={pred_ml:.0f}mL")
    print(f"T2 Faraday: measured={h2_ml:.0f}mL err={t2_err*100:.1f}% -> {'PASS' if t2 else 'FAIL'}")
    print(f"T3 ratio O2/H2={ratio:.3f} -> {'PASS' if t3 else 'FAIL'}")
    print(f"T4 stability std/mean={stab*100:.1f}% -> {'PASS' if t4 else 'FAIL'}")
    overall = t2 and t3 and t4
    print(f"OVERALL -> {'PASS' if overall else 'FAIL'}")
    return overall

if __name__ == "__main__":
    ok = check(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]))
    sys.exit(0 if ok else 1)
