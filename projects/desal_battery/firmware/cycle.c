#include "cycle.h"

void cyc_init(cyc_t *c, float tds_target, float ah_limit) {
    c->st = ST_IDLE; c->reason = R_NONE;
    c->ah = 0; c->wh_chg = 0; c->wh_dis = 0; c->t_s = 0;
    c->tds_target_ppm = tds_target; c->ah_limit = ah_limit;
    c->vmax_V = 1.0f; c->vfloor_V = 0.1f; c->timeout_s = 12 * 3600.0;
}

void cyc_start_charge(cyc_t *c) {
    c->st = ST_CHARGE; c->reason = R_NONE; c->ah = 0; c->t_s = 0;
}

void cyc_start_discharge(cyc_t *c) {
    c->st = ST_DISCHARGE; c->reason = R_NONE; c->ah = 0; c->t_s = 0;
}

cyc_state_t cyc_tick(cyc_t *c, float v, float i, float tds_ppm, float dt_s) {
    if (c->st != ST_CHARGE && c->st != ST_DISCHARGE) return c->st;
    if (i < 0) i = 0;
    c->ah += (double)i * dt_s / 3600.0;
    c->t_s += dt_s;
    if (c->st == ST_CHARGE) {
        c->wh_chg += (double)v * i * dt_s / 3600.0;
        if (v > c->vmax_V) { c->st = ST_FAULT; c->reason = R_OVERVOLT; return c->st; }
        if (tds_ppm <= c->tds_target_ppm) { c->st = ST_DONE; c->reason = R_TDS_TARGET; return c->st; }
        if (c->ah >= c->ah_limit) { c->st = ST_DONE; c->reason = R_AH_LIMIT; return c->st; }
    } else {
        c->wh_dis += (double)v * i * dt_s / 3600.0;
        if (v < c->vfloor_V && c->t_s > 60) { c->st = ST_DONE; c->reason = R_V_FLOOR; return c->st; }
    }
    if (c->t_s > c->timeout_s) { c->st = ST_FAULT; c->reason = R_TIMEOUT; }
    return c->st;
}
