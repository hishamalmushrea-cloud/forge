#pragma once
/* chaos_mesh hop engine: Q16 fixed-point Lorenz, bit-exact with chaos_mesh.py */
#include <stdint.h>

#define MESH_S      ((int64_t)65536)
#define MESH_SIG    10
#define MESH_RHO    28
#define MESH_BET_N  8
#define MESH_BET_D  3
#define MESH_DT_SH  7
#define MESH_WARM   3000
#define MESH_DWELL  50
#define MESH_NCH    8

typedef struct { int64_t x, y, z; } mesh_state_t;

int64_t mesh_fsh(int64_t v, int n);   /* floor shift, exact incl. negatives */
void mesh_step(mesh_state_t *s);      /* one Euler DT=2^-7 step */
void mesh_seed(mesh_state_t *s, const uint8_t *seed, int len);
uint8_t mesh_hop(const mesh_state_t *s);
uint8_t mesh_next(mesh_state_t *s);   /* advance DWELL steps, return hop */
