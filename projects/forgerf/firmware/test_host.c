/* Host test: ISM allow/cap + aviation/FM/distress deny + ham gate + watchdog. */
#include <stdio.h>
#include "txfw.h"

static int fails = 0;
#define CHECK(c, ...) do { \
    if (c) { printf("PASS "); printf(__VA_ARGS__); printf("\n"); } \
    else { printf("FAIL "); printf(__VA_ARGS__); printf("\n"); fails++; } } while (0)

int main(void) {
    txfw_t t;
    txfw_init(&t);
    t.freq_mhz = 433.9f;
    t.pdbm = 10;
    txfw_check(&t);
    CHECK(t.verdict, "ISM 433.9/10dBm allowed");
    t.pdbm = 20;
    txfw_check(&t);
    CHECK(!t.verdict, "ISM overpower denied");
    t.freq_mhz = 121.5f;
    t.pdbm = 0;
    txfw_check(&t);
    CHECK(!t.verdict, "aviation distress denied");
    t.freq_mhz = 100.0f;
    txfw_check(&t);
    CHECK(!t.verdict, "FM broadcast denied");
    t.freq_mhz = 406.025f;
    txfw_check(&t);
    CHECK(!t.verdict, "EPIRB 406 denied");
    t.freq_mhz = 145.0f;
    t.pdbm = 20;
    txfw_check(&t);
    CHECK(!t.verdict, "ham without license denied");
    t.ham_license = 1;
    txfw_check(&t);
    CHECK(t.verdict, "ham with license allowed");
    for (int i = 0; i < 61; i++) txfw_tick(&t, 1);
    CHECK(t.revoked, "61s carrier revoked");
    txfw_tick(&t, 0);
    CHECK(t.carrier_s == 0, "unkey resets watchdog");
    printf(fails ? "TXFW: FAIL\n" : "TXFW: ALL PASS\n");
    return fails ? 1 : 0;
}
