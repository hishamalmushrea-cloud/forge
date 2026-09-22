#include "charge.h"

#define CAP_AH 14.8f

void chg_init(chg_t *c) {
    c->duty = 200;
    c->dir = 1;
    c->duty_cap = 1000;
    c->p_old = 0;
    c->soc = 50;
    c->cv_mode = 0;
    c->fault = 0;
}

int chg_mppt_tick(chg_t *c, float v_panel, float i_panel) {
    float p = v_panel * i_panel;
    if (p > c->p_old) c->duty += c->dir * 10;
    else { c->dir = -c->dir; c->duty += c->dir * 10; }
    c->p_old = p;
    if (c->duty > c->duty_cap) c->duty = c->duty_cap;
    if (c->duty < 0) c->duty = 0;
    if (c->duty > 1000) c->duty = 1000;
    return c->duty;
}

void chg_batt_tick(chg_t *c, float v_batt, float i_batt, float temp_c, float dt_s) {
    c->soc += i_batt * dt_s / 3600.0f / CAP_AH * 100.0f;
    if (c->soc > 100) c->soc = 100;
    if (c->soc < 0) c->soc = 0;
    c->cv_mode = (v_batt >= 4.2f) ? 1 : 0;
    if (c->cv_mode && c->duty_cap > 0) c->duty_cap -= 50;
    if (!c->cv_mode && c->duty_cap < 1000) c->duty_cap += 10;
    c->fault = 0;
    if (v_batt > 4.25f) c->fault |= 1;
    if (v_batt < 3.0f) c->fault |= 2;
    if (temp_c > 45.0f) c->fault |= 4;
    if (c->fault) c->duty_cap = 0;
}
