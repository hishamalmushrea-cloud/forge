/* Host test: float-off + absorb-ramp + full-dump + brake latch/release. */
#include <stdio.h>
#include <math.h>
#include "dump.h"

static int fails = 0;
#define CHECK(c, ...) do { \
    if (c) { printf("PASS "); printf(__VA_ARGS__); printf("\n"); } \
    else { printf("FAIL "); printf(__VA_ARGS__); printf("\n"); fails++; } } while (0)

int main(void) {
    dump_t d;
    dump_init(&d);
    d.vbatt = 13.5f;
    d.rpm = 300;
    dump_tick(&d);
    CHECK(d.pwm == 0 && !d.brake, "float: all power to battery");
    d.vbatt = 14.4f;
    dump_tick(&d);
    CHECK(fabsf(d.pwm - 0.5f) < 0.05f, "absorb ramp pwm=%.2f", d.pwm);
    d.vbatt = 14.8f;
    dump_tick(&d);
    CHECK(d.pwm == 1.0f && !d.brake, "full battery: full dump, no brake yet");
    d.vbatt = 15.1f;
    dump_tick(&d);
    CHECK(d.brake && d.pwm == 1.0f, "overvolt: brake latched");
    dump_init(&d);
    d.rpm = 850;
    d.vbatt = 13.0f;
    dump_tick(&d);
    CHECK(d.brake, "overspeed: brake even at low volts");
    d.vbatt = 14.0f;
    d.rpm = 500;
    dump_tick(&d);
    CHECK(!d.brake, "calm + cool volts: brake released");
    printf(fails ? "DUMP: FAIL\n" : "DUMP: ALL PASS\n");
    return fails ? 1 : 0;
}
