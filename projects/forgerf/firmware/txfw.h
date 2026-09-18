#pragma once
/* TX firewall: refuses transmit outside allowed bands/powers.
   ISM open, ham needs license flag, aviation/FM/emergency always denied,
   watchdog revokes endless carriers. */
#include <stdint.h>

typedef struct {
    float freq_mhz, pdbm;
    uint8_t region;       /* 0=YE 1=EU 2=US */
    uint8_t ham_license;
    uint8_t verdict;      /* 0=deny 1=allow */
    uint8_t carrier_s;    /* continuous-carrier seconds */
    uint8_t revoked;
} txfw_t;

void txfw_init(txfw_t *t);
void txfw_check(txfw_t *t);
void txfw_tick(txfw_t *t, uint8_t keyed);
