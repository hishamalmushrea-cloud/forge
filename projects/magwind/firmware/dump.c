#include "dump.h"

void dump_init(dump_t *d) {
    d->vbatt = 12.8f;
    d->rpm = 0;
    d->pwm = 0;
    d->brake = 0;
}

void dump_tick(dump_t *d) {
    if (d->vbatt > 15.0f || d->rpm > 800.0f)
        d->brake = 1;
    else if (d->vbatt < 14.4f && d->rpm < 600.0f)
        d->brake = 0;
    if (d->brake)
        d->pwm = 1.0f;
    else if (d->vbatt < 14.2f)
        d->pwm = 0;
    else if (d->vbatt > 14.6f)
        d->pwm = 1.0f;
    else
        d->pwm = (d->vbatt - 14.2f) / 0.4f;
}
