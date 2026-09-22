/* Host tests: mock 4-step cycle with synthetic sensors. Build: gcc -Wall -Wextra -o test_host test_host.c cycle.c */
#include <stdio.h>
#include "cycle.h"

static int fails = 0;
#define ASSERT(c, msg) do { if (c) printf("PASS: %s\n", msg); \
    else { printf("FAIL: %s\n", msg); fails++; } } while (0)

/* Simulate charge: TDS falls linearly to target over `hours`, V=0.5, I=1.9 */
static void mock_charge(cyc_t *c, float tds0, float tds1, int hours, float v) {
    cyc_start_charge(c);
    int steps = hours * 60;
    for (int k = 0; k < steps && c->st == ST_CHARGE; k++) {
        float tds = tds0 + (tds1 - tds0) * k / (steps - 1);
        cyc_tick(c, v, 1.9f, tds, 60.0f);
    }
}

int main(void) {
    cyc_t c;
    /* 1. nominal 90% pass: 35000 -> 3500 ppm */
    cyc_init(&c, 3500, 20.0f);
    mock_charge(&c, 35000, 3500, 4, 0.5f);
    printf("[chg90] st=%d reason=%d Ah=%.2f Wh=%.2f\n", c.st, c.reason, c.ah, c.wh_chg);
    ASSERT(c.st == ST_DONE && c.reason == R_TDS_TARGET, "charge ends on TDS target");
    ASSERT(c.ah > 7.0 && c.ah < 8.2, "charge Ah ~7.6 (1.9A x 4h)");
    /* 2. discharge to floor, recovery ratio */
    cyc_start_discharge(&c);
    for (int k = 0; k < 240 && c.st == ST_DISCHARGE; k++) {
        float v = (k < 228) ? 0.43f : 0.05f;   /* plateau then collapse */
        cyc_tick(&c, v, 1.9f, 40000, 60.0f);
    }
    double rec = c.wh_dis / c.wh_chg;
    printf("[dis] st=%d reason=%d rec=%.2f\n", c.st, c.reason, rec);
    ASSERT(c.st == ST_DONE && c.reason == R_V_FLOOR, "discharge ends on V floor");
    ASSERT(rec > 0.5, "recovery ratio >50%");
    /* 3. overvoltage fault */
    cyc_init(&c, 3500, 20.0f);
    mock_charge(&c, 35000, 20000, 1, 1.5f);
    ASSERT(c.st == ST_FAULT && c.reason == R_OVERVOLT, "overvoltage trips FAULT");
    /* 4. Ah-limit backup (TDS sensor stuck high) */
    cyc_init(&c, 3500, 5.0f);
    mock_charge(&c, 35000, 34000, 4, 0.5f);
    ASSERT(c.st == ST_DONE && c.reason == R_AH_LIMIT, "Ah limit backs up TDS sensor");
    /* 5. timeout fault */
    cyc_init(&c, 1, 1e9f);
    cyc_start_charge(&c);
    for (int k = 0; k < 800 && c.st == ST_CHARGE; k++) cyc_tick(&c, 0.5f, 1.9f, 35000, 60.0f);
    ASSERT(c.st == ST_FAULT && c.reason == R_TIMEOUT, "stuck run trips timeout");
    printf(fails ? "HOST TESTS: %d FAILURES\n" : "HOST TESTS: ALL PASS [VERIFIED]\n", fails);
    return fails != 0;
}
