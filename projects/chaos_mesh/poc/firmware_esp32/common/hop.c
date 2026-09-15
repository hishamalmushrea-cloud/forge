#include "hop.h"
#include "sha256.h"

int64_t mesh_fsh(int64_t v, int n) {
    if (v >= 0) return v >> n;
    return -((((-v) + ((int64_t)1 << n) - 1) >> n));
}

static int64_t floordiv(int64_t a, int64_t b) { /* b > 0, floor semantics */
    if (a >= 0) return a / b;
    return -(((-a) + b - 1) / b);
}

/* NOTE: sequential update (new X feeds Y, new X/Y feed Z) — mirrors model. */
void mesh_step(mesh_state_t *s) {
    s->x += mesh_fsh(MESH_SIG * (s->y - s->x), MESH_DT_SH);
    s->y += mesh_fsh(mesh_fsh(s->x * (MESH_RHO * MESH_S - s->z), 16) - s->y, MESH_DT_SH);
    s->z += mesh_fsh(mesh_fsh(s->x * s->y, 16) - floordiv(MESH_BET_N * s->z, MESH_BET_D), MESH_DT_SH);
}

void mesh_seed(mesh_state_t *s, const uint8_t *seed, int len) {
    uint8_t d[32];
    sha256(seed, (uint32_t)len, d);
    uint64_t u = 0;
    for (int i = 0; i < 8; i++) u = (u << 8) | d[i];
    uint64_t span = 40 * (uint64_t)MESH_S;
    s->x = MESH_S + (int64_t)(u % span);
    s->y = MESH_S + (int64_t)((u >> 3) % span);
    s->z = MESH_S + (int64_t)((u >> 5) % span);
    for (int i = 0; i < MESH_WARM; i++) mesh_step(s);
}

uint8_t mesh_hop(const mesh_state_t *s) {
    int wing = (s->y > 0) ? 0 : 1;
    int64_t az = (s->z >= 0) ? s->z : -s->z;
    int bin = (int)((mesh_fsh(az, 16) / 6) % 4);
    return (uint8_t)((wing * 4 + bin) % MESH_NCH);
}

uint8_t mesh_next(mesh_state_t *s) {
    for (int i = 0; i < MESH_DWELL; i++) mesh_step(s);
    return mesh_hop(s);
}
