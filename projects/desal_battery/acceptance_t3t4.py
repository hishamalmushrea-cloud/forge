#!/usr/bin/env python3
"""MUSHREA FORGE — T3/T4 acceptance for desalination prototype.
T3 file: charge CSV (t_s,V,I,TDS_ppm) + volume_L -> removal% + Wh/L vs Pasta anchor 0.29+-30%.
T4 args: passes ppm_final net_Wh_per_L -> <1000ppm and <3 kWh/m3.
--selftest: nominal (PASS/PASS) + weak-faraday fault (FAIL). STATUS: EXECUTED here on SIMULATED data.
Usage: acceptance_t3t4.py T3 charge.csv volume_L | T4 passes ppm net_Wh_L | --selftest
"""
import csv, sys

def t3(path, vol_L):
    rows = list(csv.DictReader(open(path)))
    wh = sum(float(r["V"]) * float(r["I"]) * 60 / 3600 for r in rows[1:]) / vol_L
    tds0, tds1 = float(rows[0]["TDS_ppm"]), float(rows[-1]["TDS_ppm"])
    rem = 1 - tds1 / tds0
    ok_r = 0.20 <= rem <= 0.30
    ok_e = abs(wh - 0.29) / 0.29 <= 0.30
    print(f"T3: removal={rem*100:.1f}% Wh/L={wh:.3f} -> {'PASS' if ok_r and ok_e else 'FAIL'}")
    return ok_r and ok_e

def t4(passes, ppm, net):
    ok = ppm < 1000 and net < 3.0
    print(f"T4: passes={passes} ppm={ppm} net={net} -> {'PASS' if ok else 'FAIL'}")
    return ok

def gen(path, removal, wh_per_L, vol=1.0, minutes=240):
    # synthesize a charge run hitting (removal, wh_per_L)
    q_C = wh_per_L * vol * 3600 / 0.5
    i = q_C / (minutes * 60)
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["t_s", "V", "I", "TDS_ppm"])
        for m in range(minutes + 1):
            tds = 35000 * (1 - removal * m / minutes)
            w.writerow([m * 60, 0.5, round(i, 3), round(tds)])
    return path

def selftest():
    gen("sim_t3_nominal.csv", 0.25, 0.29)
    gen("sim_t3_fault.csv", 0.12, 0.29)   # weak faraday: same energy, half removal
    a = t3("sim_t3_nominal.csv", 1.0)
    b = t3("sim_t3_fault.csv", 1.0)
    c = t4(2, 350, 2.13)
    d = t4(2, 2500, 2.13)
    print(f"SELFTEST: T3nom={'PASS' if a else 'FAIL'} T3fault_detected={not b} T4nom={'PASS' if c else 'FAIL'} T4fault_detected={not d}")
    assert a and not b and c and not d
    print("V1/V2 acceptance pipeline [VERIFIED]")

if __name__ == "__main__":
    if sys.argv[1] == "--selftest":
        selftest()
    elif sys.argv[1] == "T3":
        sys.exit(0 if t3(sys.argv[2], float(sys.argv[3])) else 1)
    elif sys.argv[1] == "T4":
        sys.exit(0 if t4(int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])) else 1)
