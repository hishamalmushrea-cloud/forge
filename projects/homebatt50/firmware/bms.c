#include "bms.h"

void bms_init(bms_t *b) {
    for (int i = 0; i < 4; i++) b->cell[i] = 3.3f;
    b->pack_i = 0;
    b->temp = 25;
    b->soc = 50;
    b->bal_mask = 0;
    b->fault = 0;
    b->chg_fet = 1;
    b->dsg_fet = 1;
}

void bms_tick(bms_t *b, float dt_s) {
    b->soc += b->pack_i * dt_s / 3600.0f / 50.0f * 100.0f;
    if (b->soc > 100) b->soc = 100;
    if (b->soc < 0) b->soc = 0;
    float mn = b->cell[0];
    for (int i = 1; i < 4; i++)
        if (b->cell[i] < mn) mn = b->cell[i];
    b->bal_mask = 0;
    for (int i = 0; i < 4; i++)
        if (b->cell[i] > 3.4f && (b->cell[i] - mn) > 0.03f)
            b->bal_mask |= (uint8_t)(1u << i);
    uint8_t ov = 0, uv = 0;
    for (int i = 0; i < 4; i++) {
        if (b->cell[i] > 3.65f) ov = 1;
        if (b->cell[i] < 2.5f) uv = 1;
    }
    uint8_t ot = (b->temp > 55.0f) ? 1 : 0;
    uint8_t occ = (b->pack_i > 50.0f) ? 1 : 0;
    uint8_t ocd = (b->pack_i < -100.0f) ? 1 : 0;
    b->fault = (uint8_t)(ov | (uv << 1) | (ot << 2) | ((occ | ocd) << 3));
    b->chg_fet = (uint8_t)(!(ov || ot || occ));
    b->dsg_fet = (uint8_t)(!(uv || ot || ocd));
}
