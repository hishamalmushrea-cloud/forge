/* Real-HW HAL (SX1262 FSK via RadioLib).
   UNCOMPILED HERE — compile in Arduino IDE with RadioLib installed.
   Verify calls against your RadioLib version's SX1262 FSK examples. */
#include <RadioLib.h>
#include "radio_hal.h"

/* ESP32 example wiring — adjust to your board */
#define PIN_NSS 5
#define PIN_DIO1 4
#define PIN_RST 14
#define PIN_BUSY 27

SX1262 radio = new Module(PIN_NSS, PIN_DIO1, PIN_RST, PIN_BUSY);
static int last_rssi = -120;

void hal_init(void) {
    /* FSK 50 kbps: 20B packet airtime ~4ms (fits 100ms slot) */
    radio.beginFSK(433.1, 50.0, 25.0, 100.0, 10, 8);
}

void hal_set_channel(uint8_t ch) {
    radio.setFrequency(433.1f + 0.2f * (ch % 8));
}

int hal_tx(const uint8_t *pkt, int len) {
    int16_t st = radio.transmit((uint8_t *)pkt, (size_t)len);
    return (st == RADIOLIB_ERR_NONE) ? 0 : -1;
}

int hal_rx(uint8_t *pkt, int maxlen, int timeout_ms) {
    (void)timeout_ms;
    size_t len = (size_t)maxlen;
    int16_t st = radio.receive(pkt, &len);
    if (st == RADIOLIB_ERR_NONE) {
        last_rssi = (int)radio.getRSSI();
        return (int)len;
    }
    return -1;
}

int hal_jammed(uint8_t ch) {
    (void)ch;
    return 0;
}

int hal_rssi(void) { return last_rssi; }
