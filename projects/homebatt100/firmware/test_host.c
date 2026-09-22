/* Host test: balance bleeds runner + spread shrinks + OV/UV/OT/OC + SOC exact. */
#include <stdio.h>
#include <math.h>
#include "bms.h"

static int fails = 0;
#define CHECK(c, ...) do { \
    if (c) { printf("PASS "); printf(__VA_ARGS__); printf("\n"); } \
    else { printf("FAIL "); printf(__VA_ARGS__); printf("\n"); fails++; } } while (0)

int main(void) {
    bms_t b;
    bms_init(&b);
    b.cell[0] = 3.30f; b.cell[1] = 3.32f; b.cell[2] = 3.28f; b.cell[3] = 3.45f;
    b.pack_i = 5.0f;
    bms_tick(&b, 1.0f);
    CHECK(b.bal_mask == 0x08, "bleeds runner cell4 (mask=%02x)", b.bal_mask);
    float spread0 = 3.45f - 3.28f;
    for (int t = 0; t < 50; t++) {
        bms_tick(&b, 1.0f);
        for (int i = 0; i < 4; i++)
            if (b.bal_mask & (1u << i)) b.cell[i] -= 0.002f;
    }
    float mn = b.cell[0], mx = b.cell[0];
    for (int i = 1; i < 4; i++) {
        if (b.cell[i] < mn) mn = b.cell[i];
        if (b.cell[i] > mx) mx = b.cell[i];
    }
    CHECK(mx - mn < spread0, "spread %.0fmV -> %.0fmV", spread0 * 1000, (mx - mn) * 1000);
    bms_init(&b);
    bms_tick(&b, 1.0f);
    CHECK(b.bal_mask == 0, "balanced pack: no bleed");

    bms_init(&b);
    b.cell[2] = 3.66f;
    bms_tick(&b, 1.0f);
    CHECK(!b.chg_fet && (b.fault & 1), "OV blocks charge");
    bms_init(&b);
    b.cell[0] = 2.49f;
    bms_tick(&b, 1.0f);
    CHECK(!b.dsg_fet && (b.fault & 2), "UV blocks discharge");
    bms_init(&b);
    b.temp = 60.0f;
    bms_tick(&b, 1.0f);
    CHECK(!b.chg_fet && !b.dsg_fet && (b.fault & 4), "OT blocks all");
    bms_init(&b);
    b.pack_i = 60.0f;
    bms_tick(&b, 1.0f);
    CHECK(!b.chg_fet && (b.fault & 8), "OC-charge trip");
    bms_init(&b);
    b.pack_i = -120.0f;
    bms_tick(&b, 1.0f);
    CHECK(!b.dsg_fet && (b.fault & 8), "OC-discharge trip");

    bms_init(&b);
    b.soc = 20.0f;
    b.pack_i = 5.0f;
    bms_tick(&b, 3600.0f);
    CHECK(fabsf(b.soc - 25.0f) < 0.01f, "SOC 20%% -> %.2f%% exact", b.soc);

    printf(fails ? "BMS: FAIL\n" : "BMS: ALL PASS\n");
    return fails ? 1 : 0;
}
