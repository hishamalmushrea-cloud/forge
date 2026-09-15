#include "mesh.h"
#include <string.h>

uint16_t mesh_crc(const frame_t *f) {
    uint16_t c = 0xFFFF;
    const uint8_t *d = (const uint8_t *)f;
    for (int i = 0; i < 8 + f->len; i++) {
        c ^= (uint16_t)d[i] << 8;
        for (int k = 0; k < 8; k++)
            c = (c & 0x8000) ? (uint16_t)((c << 1) ^ 0x1021) : (uint16_t)(c << 1);
    }
    return c;
}

void mesh_init(mesh_t *m, uint8_t id, const uint8_t *netseed, int slen) {
    memset(m, 0, sizeof(*m));
    m->id = id;
    mesh_seed(&m->sched, netseed, slen);
}

uint8_t mesh_slot_ch(mesh_t *m) {
    return mesh_next(&m->sched);
}

static int seen_has(mesh_t *m, uint16_t k);

static void seen_add(mesh_t *m, uint16_t k) {
    if (seen_has(m, k)) return;
    if (m->seen_n < MESH_SEEN) m->seen[m->seen_n++] = k;
    else { memmove(m->seen, m->seen + 1, (MESH_SEEN - 1) * 2); m->seen[MESH_SEEN - 1] = k; }
}

int mesh_send(mesh_t *m, uint8_t dst, const uint8_t *data, int len, frame_t out[4]) {
    int n = (len + MESH_PLEN - 1) / MESH_PLEN;
    if (n > 4 || n < 1) return -1;
    uint8_t mid = m->next_msgid++;
    seen_add(m, (uint16_t)((uint16_t)m->id << 8) | mid);  /* origin: no ping-pong */
    for (int i = 0; i < n; i++) {
        frame_t *f = &out[i];
        memset(f, 0, sizeof(*f));
        f->src = m->id;
        f->dst = dst;
        f->msgid = mid;
        f->ttl = 6;
        f->frag_tot = (uint8_t)n;
        f->frag_idx = (uint8_t)i;
        f->len = (uint16_t)((len - i * MESH_PLEN > MESH_PLEN) ? MESH_PLEN : (len - i * MESH_PLEN));
        memcpy(f->pl, data + i * MESH_PLEN, f->len);
        f->crc = mesh_crc(f);
    }
    return n;
}

static int seen_has(mesh_t *m, uint16_t k) {
    for (int i = 0; i < m->seen_n; i++)
        if (m->seen[i] == k) return 1;
    return 0;
}

int mesh_on_rx(mesh_t *m, const frame_t *f, frame_t *fwd) {
    if (f->len > MESH_PLEN || f->frag_idx >= f->frag_tot || f->frag_tot > 4) return 0;
    if (mesh_crc(f) != f->crc) return 0;
    uint16_t k = (uint16_t)((uint16_t)f->src << 8) | f->msgid;
    if (seen_has(m, k)) { m->dup_drop++; return 0; }
    seen_add(m, k);
    if (f->dst == m->id) { m->rx_ok++; return 1; }
    if (f->ttl == 0) return 0;
    *fwd = *f;
    fwd->ttl--;
    fwd->crc = mesh_crc(fwd);
    m->fwds++;
    return 2;
}
