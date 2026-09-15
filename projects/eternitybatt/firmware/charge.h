#pragma once
/* Solar MPPT + CC/CV + fuel gauge + safety for the eternity station (1S4P 18650). */
#include <stdint.h>

typedef struct {
    int duty, dir, duty_cap;
    float p_old, soc;
    uint8_t cv_mode, fault;  /* fault bits: 1 OV, 2 UV, 4 OT */
} chg_t;

void chg_init(chg_t *c);
int chg_mppt_tick(chg_t *c, float v_panel, float i_panel);
void chg_batt_tick(chg_t *c, float v_batt, float i_batt, float temp_c, float dt_s);
