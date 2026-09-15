#include "radio_hal.h"
#include "hal_loopback.h"
#include <string.h>

static uint8_t cur_ch = 0, air[64];
static int air_len = 0, air_ch = 0, air_on = 0;
static uint8_t jam_mask = 0;
static int outage = 0;

void hal_init(void) {}
void hal_set_channel(uint8_t ch) { cur_ch = ch; }

int hal_tx(const uint8_t *pkt, int len) {
    if (len > (int)sizeof(air)) len = sizeof(air);
    memcpy(air, pkt, len);
    air_len = len;
    air_ch = cur_ch;
    air_on = 1;
    return 0;
}

int hal_rx(uint8_t *pkt, int maxlen, int timeout_ms) {
    (void)maxlen;
    (void)timeout_ms;
    if (!air_on || outage) return -1;
    if (air_ch != cur_ch) return -1;
    if (jam_mask & (uint8_t)(1u << cur_ch)) return -1;
    memcpy(pkt, air, air_len);
    air_on = 0;
    return air_len;
}

int hal_jammed(uint8_t ch) { return (jam_mask >> ch) & 1; }
int hal_rssi(void) { return -70; }

void loopback_set_jam(uint8_t mask) { jam_mask = mask; }
void loopback_outage(int on) { outage = on; }
void loopback_corrupt_air(void) { if (air_on) air[3] ^= 0xFF; }
