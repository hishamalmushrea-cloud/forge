#pragma once
/* Synchronized hopping-mesh node: shared Q16 schedule + flood + seen-cache + frag. */
#include <stdint.h>
#include "hop.h"

#define MESH_MAXN 8
#define MESH_SEEN 16
#define MESH_PLEN 187
#define MESH_TRIES 3

typedef struct {
    uint8_t src, dst, msgid, ttl, frag_tot, frag_idx;
    uint16_t len;
    uint8_t pl[MESH_PLEN];
    uint16_t crc;
} frame_t;

typedef struct {
    uint8_t id;
    mesh_state_t sched;
    uint16_t seen[MESH_SEEN];
    uint8_t seen_n;
    uint8_t nbrs[MESH_MAXN];
    uint8_t nnbr;
    uint8_t next_msgid;
    uint32_t tx, fwds, rx_ok, dup_drop;
} mesh_t;

void mesh_init(mesh_t *m, uint8_t id, const uint8_t *netseed, int slen);
uint8_t mesh_slot_ch(mesh_t *m);   /* call EXACTLY once per node per slot (lockstep) */
int mesh_send(mesh_t *m, uint8_t dst, const uint8_t *data, int len, frame_t out[4]);
/* returns 1=accepted, 2=forward(fill fwd), 0=drop */
int mesh_on_rx(mesh_t *m, const frame_t *f, frame_t *fwd);
uint16_t mesh_crc(const frame_t *f);
