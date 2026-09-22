#pragma once
/* Loopback test controls (emulator only, not compiled for ESP32) */
#include <stdint.h>

void loopback_set_jam(uint8_t mask);   /* bit ch = jammed */
void loopback_outage(int on);          /* drop everything */
void loopback_corrupt_air(void);       /* flip a payload byte (forgery test) */
