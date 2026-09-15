#!/usr/bin/env python3
"""MUSHREA FORGE — Virtual commissioning: simulate Arduino logs, run acceptance.
CASE A (nominal): 4A + noise, 30 min -> volumes near theory -> expect PASS.
CASE B (fault: gas leak): H2 volume 35% low -> expect FAIL on T2.
STATUS of generated data: SIMULATED (seeded noise) — validates the pipeline, not the physics.
"""
import random
from acceptance import check

F = 96485.0
HDR = "t_s,Vcell_V,ImA,coulombs,H2_pred_mL,relay"

def gen_csv(path, i_nom, v_nom, seconds, step=10, seed=7):
    rnd = random.Random(seed)
    q = 0.0
    with open(path, "w") as f:
        f.write(HDR + "\n")
        for t in range(0, seconds + 1, step):
            i = rnd.gauss(i_nom, 0.05)
            v = rnd.gauss(v_nom, 0.03)
            q += i * step
            h2 = q / (2 * F) * 24450.0
            f.write(f"{t},{v:.3f},{i*1000:.1f},{q:.1f},{h2:.1f},1\n")
    return q / (2 * F) * 24450.0

print("=== CASE A: nominal (expect PASS) ===")
predA = gen_csv("sim_nominal.csv", 4.0, 2.0, 1800)
okA = check("sim_nominal.csv", predA * 0.97, predA * 0.97 / 2)
print("=== CASE B: H2 leak fault (expect FAIL) ===")
predB = gen_csv("sim_fault.csv", 4.0, 2.0, 1800, seed=21)
okB = check("sim_fault.csv", predB * 0.65, predB * 0.65 / 2)
print(f"VIRTUAL COMMISSIONING: nominal={'PASS' if okA else 'FAIL'} fault_detected={not okB}")
assert okA and not okB, "commissioning logic broken"
print("V1 pipeline nominal PASS + V2 fault detection PASS [VERIFIED]")
