#!/usr/bin/env python3
"""MUSHREA FORGE — T4 acceptance: measured Vcap week vs simulation.
Usage: python3 acceptance_t4.py measured.csv   (columns t_h,Vcap_V, hourly)
Checks: T4a min Vcap >= 2.0V | T4b mean|dev| vs sim trace <= 0.30V
--selftest: nominal (expect PASS) + sag fault (expect FAIL). STATUS: EXECUTED here on SIMULATED data.
"""
import csv, json, sys, random

SIM = json.load(open("results.json"))["week_trace_V"]

def check(path):
    rows = list(csv.DictReader(open(path)))
    meas = [float(r["Vcap_V"]) for r in rows]
    n = min(len(meas), len(SIM))
    t4a = min(meas) >= 2.0
    dev = sum(abs(meas[i] - SIM[i]) for i in range(n)) / n
    t4b = dev <= 0.30
    print(f"{path}: n={n} minV={min(meas):.2f} meanDev={dev:.3f} -> T4a {'PASS' if t4a else 'FAIL'} T4b {'PASS' if t4b else 'FAIL'}")
    return t4a and t4b

def write_csv(path, series):
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["t_h", "Vcap_V"])
        for i, v in enumerate(series):
            w.writerow([i, round(v, 3)])

def selftest():
    rnd = random.Random(11)
    nom = [v + rnd.gauss(0, 0.05) for v in SIM]
    fault = [v - (0.9 if 60 <= i <= 80 else 0.0) + rnd.gauss(0, 0.05) for i, v in enumerate(SIM)]
    write_csv("sim_t4_nominal.csv", nom)
    write_csv("sim_t4_fault.csv", fault)
    ok_nom = check("sim_t4_nominal.csv")
    ok_flt = check("sim_t4_fault.csv")
    print(f"SELFTEST: nominal={'PASS' if ok_nom else 'FAIL'} fault_detected={not ok_flt}")
    assert ok_nom and not ok_flt
    print("V1/V2 acceptance pipeline [VERIFIED]")

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        selftest()
    else:
        sys.exit(0 if check(sys.argv[1]) else 1)
