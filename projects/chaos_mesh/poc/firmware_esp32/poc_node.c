#include "poc_node.h"
#include "radio_hal.h"
#include "sha256.h"
#include <string.h>

static uint16_t crc16(const uint8_t *d, int n) {
    uint16_t c = 0xFFFF;
    for (int i = 0; i < n; i++) {
        c ^= (uint16_t)d[i] << 8;
        for (int k = 0; k < 8; k++)
            c = (c & 0x8000) ? (uint16_t)((c << 1) ^ 0x1021) : (uint16_t)(c << 1);
    }
    return c;
}

void poc_init(poc_t *p, uint8_t role, const uint8_t *seed, int slen, const uint8_t *key16) {
    memset(p, 0, sizeof(*p));
    p->role = role;
    p->slen = slen > 24 ? 24 : slen;
    memcpy(p->seed, seed, p->slen);
    memcpy(p->key, key16, 16);
    mesh_seed(&p->eng, seed, slen);
}

void poc_build(const poc_t *p, const uint8_t *pl, uint8_t *pkt) {
    pkt[0] = (uint8_t)((p->slot >> 8) & 0xFF);
    pkt[1] = (uint8_t)(p->slot & 0xFF);
    memcpy(pkt + 2, pl, POC_PLEN);
    uint8_t mac[32];
    hmac_sha256(p->key, 16, pkt, 2 + POC_PLEN, mac);
    memcpy(pkt + 2 + POC_PLEN, mac, POC_MACLEN);
    uint16_t c = crc16(pkt, 2 + POC_PLEN + POC_MACLEN);
    pkt[18] = (uint8_t)(c >> 8);
    pkt[19] = (uint8_t)(c & 0xFF);
}

int poc_verify(poc_t *p, const uint8_t *pkt, uint8_t *pl_out, uint32_t *slot_out) {
    (void)p;
    uint16_t c = (uint16_t)((uint16_t)pkt[18] << 8) | pkt[19];
    if (crc16(pkt, 18) != c) return 0;
    uint8_t mac[32];
    hmac_sha256(p->key, 16, pkt, 2 + POC_PLEN, mac);
    if (memcmp(mac, pkt + 10, POC_MACLEN) != 0) return 0;
    if (pl_out) memcpy(pl_out, pkt + 2, POC_PLEN);
    if (slot_out) *slot_out = ((uint32_t)pkt[0] << 8) | pkt[1];
    return 1;
}

void poc_node_tick(poc_t *p, const uint8_t payload[POC_PLEN]) {
    uint8_t ch = mesh_next(&p->eng);
    uint8_t pkt[POC_PKT];
    poc_build(p, payload, pkt);
    hal_set_channel(ch);
    hal_tx(pkt, POC_PKT);
    p->tx_n++;
    p->slot++;
}

/* Rebuild engine state for expected slot e (e mesh_next calls after reseed). */
static void eng_ffwd(poc_t *p, uint32_t e) {
    mesh_seed(&p->eng, p->seed, p->slen);
    for (uint32_t i = 0; i < e; i++) mesh_next(&p->eng);
}

int poc_gw_tick(poc_t *p, uint8_t pl_out[POC_PLEN], uint32_t *rxslot, uint8_t *rxch) {
    uint8_t pkt[POC_PKT], pl[POC_PLEN];
    uint32_t s;
    if (p->state == 0) {  /* SEARCH: scan all channels */
        for (uint8_t ch = 0; ch < 8; ch++) {
            hal_set_channel(ch);
            if (hal_rx(pkt, sizeof(pkt), 5) == POC_PKT && poc_verify(p, pkt, pl, &s)) {
                eng_ffwd(p, s + 1);
                p->slot = s + 1;
                p->state = 1;
                p->rx_ok++;
                p->hist_ch[0] = ch;
                p->hist_ch[1] = ch;
                if (pl_out) memcpy(pl_out, pl, POC_PLEN);
                if (rxslot) *rxslot = s;
                if (rxch) *rxch = ch;
                return 1;
            }
        }
        return 0;
    }
    /* LOCKED: candidate channels from clones (engine untouched until accept) */
    mesh_state_t c0 = p->eng;
    uint8_t ch_now = mesh_next(&c0);
    uint8_t ch_p1 = mesh_next(&c0);
    uint8_t ch_p2 = mesh_next(&c0);
    uint8_t cands[5] = {ch_now, ch_p1, p->hist_ch[0], ch_p2, p->hist_ch[1]};
    for (int i = 0; i < 5; i++) {
        hal_set_channel(cands[i]);
        if (hal_rx(pkt, sizeof(pkt), 5) == POC_PKT && poc_verify(p, pkt, pl, &s)) {
            int32_t off = (int32_t)s - (int32_t)p->slot;
            if (off >= -2 && off <= 2) {
                if (off < 0) {
                    eng_ffwd(p, s + 1);
                } else {
                    for (int32_t k = 0; k < off + 1; k++) mesh_next(&p->eng);
                }
                if (off != 0) p->resyncs++;
                p->hist_ch[1] = p->hist_ch[0];
                p->hist_ch[0] = cands[i];
                p->slot = s + 1;
                p->rx_ok++;
                if (pl_out) memcpy(pl_out, pl, POC_PLEN);
                if (rxslot) *rxslot = s;
                if (rxch) *rxch = cands[i];
                return 1;
            }
        }
    }
    /* miss: advance lockstep (node TX'd, we lost it) */
    mesh_next(&p->eng);
    p->slot++;
    return 0;
}
