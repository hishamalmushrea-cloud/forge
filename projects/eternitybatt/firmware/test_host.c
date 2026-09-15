/* Host test: MPPT tracks synthetic IV + retracks + CC/CV + gauge + faults. */
#include <stdio.h>
#include <math.h>
#include "charge.h"

static int fails = 0;
#define CHECK(c, ...) do { \
    if (c) { printf("PASS "); printf(__VA_ARGS__); printf("\n"); } \
    else { printf("FAIL "); printf(__VA_ARGS__); printf("\n"); fails++; } } while (0)

/* parabola plant MPP at 9/sqrt(3)=5.196V */
int main(void) {
    chg_t c;
    chg_init(&c);
    float v = 0;
    for (int t = 0; t < 300; t++) {
        v = c.duty / 1000.0f * 9.0f;
        float i = 1.0f * (1.0f - (v / 9.0f) * (v / 9.0f));
        chg_mppt_tick(&c, v, i);
    }
    CHECK(fabsf(v - 5.196f) < 0.6f, "MPPT locks %.2fV (want 5.20)", v);
    for (int t = 0; t < 200; t++) {
        v = c.duty / 1000.0f * 9.0f;
        float i = 0.5f * (1.0f - (v / 9.0f) * (v / 9.0f));
        chg_mppt_tick(&c, v, i);
    }
    CHECK(fabsf(v - 5.196f) < 0.6f, "MPPT retracks after shade %.2fV", v);

    chg_init(&c);
    for (int t = 0; t < 120; t++)
        chg_batt_tick(&c, 3.6f + t * 0.01f, 1.0f, 25.0f, 30.0f);
    CHECK(c.cv_mode == 1 && c.duty_cap < 1000, "CC->CV taper (cap=%d)", c.duty_cap);
    CHECK(fabsf(c.soc - (50 + 120 * 30.0f / 3600.0f / 14.8f * 100)) < 0.2f,
          "gauge %.2f%% exact", c.soc);

    chg_init(&c);
    chg_batt_tick(&c, 4.30f, 0, 25, 1);
    CHECK(c.fault == 1 && c.duty_cap == 0, "OV trip");
    chg_init(&c);
    chg_batt_tick(&c, 2.90f, -0.5f, 25, 1);
    CHECK(c.fault == 2, "UV trip");
    chg_init(&c);
    chg_batt_tick(&c, 3.9f, 1.0f, 50, 1);
    CHECK(c.fault == 4, "OT trip");

    printf(fails ? "CHARGER: FAIL\n" : "CHARGER: ALL PASS\n");
    return fails ? 1 : 0;
}
