#include "txfw.h"

void txfw_init(txfw_t *t) {
    t->freq_mhz = 433.9f;
    t->pdbm = 10;
    t->region = 0;
    t->ham_license = 0;
    t->verdict = 0;
    t->carrier_s = 0;
    t->revoked = 0;
}

static uint8_t in_band(float f, float lo, float hi) {
    return (f >= lo && f <= hi) ? 1 : 0;
}

void txfw_check(txfw_t *t) {
    float f = t->freq_mhz;
    t->verdict = 0;
    if (in_band(f, 121.4f, 121.6f) || in_band(f, 242.9f, 243.1f) ||
        in_band(f, 405.9f, 406.1f))
        return; /* distress: never */
    if (in_band(f, 108, 137) || in_band(f, 87, 108))
        return; /* aviation + FM broadcast */
    if (in_band(f, 433.05f, 434.79f)) {
        if (t->pdbm <= 10) t->verdict = 1;
        return;
    }
    if (in_band(f, 868, 868.6f)) {
        if (t->pdbm <= 14) t->verdict = 1;
        return;
    }
    if (in_band(f, 2400, 2483.5f)) {
        if (t->pdbm <= 20) t->verdict = 1;
        return;
    }
    if (t->ham_license &&
        (in_band(f, 144, 146) || in_band(f, 430, 440))) {
        if (t->pdbm <= 30) t->verdict = 1;
    }
}

void txfw_tick(txfw_t *t, uint8_t keyed) {
    if (!keyed) {
        t->carrier_s = 0;
        return;
    }
    if (t->carrier_s < 255) t->carrier_s++;
    if (t->carrier_s > 60) t->revoked = 1; /* endless carrier = jam-like */
}
