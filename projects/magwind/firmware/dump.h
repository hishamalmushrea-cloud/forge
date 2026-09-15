#pragma once
/* Wind dump-load controller: absorb excess + brake on overvolt/overspeed.
   NEVER open-circuits the turbine: unloaded windmills overspeed and die. */
#include <stdint.h>

typedef struct {
    float vbatt;
    float rpm;
    float pwm;      /* 0..1 dump duty */
    uint8_t brake;  /* relay: shorts turbine via dump resistor */
} dump_t;

void dump_init(dump_t *d);
void dump_tick(dump_t *d);
