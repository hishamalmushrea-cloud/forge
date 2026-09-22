#pragma once
/* PoC node/gateway logic — shared by ESP32 (.ino) and host emulator. */
#include <stdint.h>
#include "hop.h"

#define POC_ROLE_NODE 0
#define POC_ROLE_GW   1
#define POC_PLEN      8
#define POC_MACLEN    8
#define POC_PKT       (2 + POC_PLEN + POC_MACLEN + 2)  /* slot,payload,mac,crc = 20 */

typedef struct {
    uint8_t role, state;      /* state: 0 SEARCH, 1 LOCKED */
    uint32_t slot;
    mesh_state_t eng;
    uint8_t seed[24];
    int slen;
    uint8_t key[16];
    uint8_t hist_ch[2];       /* last 2 rx channels (window past) */
    uint32_t tx_n, rx_ok, resyncs;
} poc_t;

void poc_init(poc_t *p, uint8_t role, const uint8_t *seed, int slen, const uint8_t *key16);
void poc_node_tick(poc_t *p, const uint8_t payload[POC_PLEN]);
int poc_gw_tick(poc_t *p, uint8_t pl_out[POC_PLEN], uint32_t *rxslot, uint8_t *rxch);
void poc_build(const poc_t *p, const uint8_t *pl, uint8_t *pkt);
int poc_verify(poc_t *p, const uint8_t *pkt, uint8_t *pl_out, uint32_t *slot_out);
