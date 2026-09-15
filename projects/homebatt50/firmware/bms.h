#pragma once
/* 4S 50Ah LiFePO4 supervisor: balance + OV/UV/OT/OC + SOC (mirrors HW BMS logic). */
#include <stdint.h>

typedef struct {
    float cell[4];
    float pack_i;   /* +charge, -discharge (A) */
    float temp;     /* C */
    float soc;      /* 0..100 */
    uint8_t bal_mask, fault, chg_fet, dsg_fet;
} bms_t;

void bms_init(bms_t *b);
void bms_tick(bms_t *b, float dt_s);
