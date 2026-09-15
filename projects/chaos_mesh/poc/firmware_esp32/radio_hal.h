#pragma once
/* Radio HAL: real impl = hal_sx1262_radiolib.cpp (Arduino), test impl = hal_loopback.c */
#include <stdint.h>

void hal_init(void);
void hal_set_channel(uint8_t ch);              /* 0..7 -> 433.1 + 0.2*ch MHz */
int hal_tx(const uint8_t *pkt, int len);       /* 0 ok */
int hal_rx(uint8_t *pkt, int maxlen, int timeout_ms); /* bytes, or -1 timeout */
int hal_jammed(uint8_t ch);                    /* 1 if jammed now (0 on real HW) */
int hal_rssi(void);                            /* last RSSI dBm */
