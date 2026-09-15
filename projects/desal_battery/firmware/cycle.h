#ifndef CYCLE_H
#define CYCLE_H
/* MUSHREA FORGE — desalination 4-step cycle controller (platform-independent).
 * STATUS: COMPILED + UNIT-TESTED on host (gcc). Arduino port NOT EXECUTED. */

typedef enum { ST_IDLE, ST_CHARGE, ST_DISCHARGE, ST_DONE, ST_FAULT } cyc_state_t;
typedef enum { R_NONE, R_TDS_TARGET, R_AH_LIMIT, R_V_FLOOR, R_OVERVOLT, R_TIMEOUT } cyc_reason_t;

typedef struct {
    cyc_state_t st;
    cyc_reason_t reason;
    double ah;            /* charge accumulated this phase */
    double wh_chg, wh_dis;
    double t_s;           /* phase elapsed */
    /* limits (set per run) */
    float tds_target_ppm;
    float ah_limit;
    float vmax_V;         /* overvoltage fault (water splitting guard) */
    float vfloor_V;       /* discharge end */
    double timeout_s;
} cyc_t;

void cyc_init(cyc_t *c, float tds_target, float ah_limit);
void cyc_start_charge(cyc_t *c);
void cyc_start_discharge(cyc_t *c);
/* tick during CHARGE: v,i>0 charging. tick during DISCHARGE: v,i>0 discharging. */
cyc_state_t cyc_tick(cyc_t *c, float v, float i, float tds_ppm, float dt_s);

#endif
