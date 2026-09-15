/* End-to-end PoC logic test: node<->gateway over scripted air (jam/outage/forge). */
#include <stdio.h>
#include <string.h>
#include "poc_node.h"
#include "radio_hal.h"
#include "hal_loopback.h"

static int fails = 0;
#define CHECK(c, ...) do { \
    if (c) { printf("PASS "); printf(__VA_ARGS__); printf("\n"); } \
    else { printf("FAIL "); printf(__VA_ARGS__); printf("\n"); fails++; } } while (0)

int main(void) {
    static const uint8_t SEED[] = "FORGE-mesh-seed-01";
    static const uint8_t KEY[16] = "pair-key-16bytes";
    poc_t node, gw;
    hal_init();
    poc_init(&node, POC_ROLE_NODE, SEED, 18, KEY);
    poc_init(&gw, POC_ROLE_GW, SEED, 18, KEY);
    uint8_t pl[POC_PLEN];
    uint32_t rs;
    uint8_t rc;
    int ok_clean = 0, ok_jam = 0, ok_post = 0, n_post = 0;

    for (int t = 0; t < 330; t++) {
        if (t == 100) loopback_set_jam(0x0F);              /* barrage ch0-3 */
        if (t == 200) { loopback_set_jam(0x00); loopback_outage(1); }
        if (t == 230) { loopback_outage(0); gw.slot += 2; } /* drifted +2: force resync path */
        memset(pl, 0, sizeof(pl));
        pl[0] = (uint8_t)((t >> 8) & 0xFF);
        pl[1] = (uint8_t)(t & 0xFF);
        uint32_t before = gw.rx_ok;
        poc_node_tick(&node, pl);
        if (t == 150) loopback_corrupt_air();              /* forged bytes on air */
        int got = poc_gw_tick(&gw, pl, &rs, &rc);
        if (t == 0) CHECK(gw.state == 1, "gateway SEARCH->LOCKED on slot 0");
        if (t == 150) CHECK(!got && gw.rx_ok == before, "forged packet rejected");
        if (t < 100) ok_clean += got;
        else if (t < 200) ok_jam += got;
        else if (t >= 230) { ok_post += got; n_post++; }
    }
    CHECK(ok_clean >= 95, "clean PDR %d/100", ok_clean);
    CHECK(ok_jam >= 30, "barrage50 PDR %d/100", ok_jam);
    CHECK(ok_post >= 95, "post-outage PDR %d/%d", ok_post, n_post);
    CHECK(gw.resyncs == 1, "exactly 1 resync event (forced drift), got %u", gw.resyncs);
    printf(fails ? "EMULATOR: FAIL\n" : "EMULATOR: ALL PASS\n");
    return fails ? 1 : 0;
}
