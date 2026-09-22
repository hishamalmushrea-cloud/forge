/* mesh_poc_gateway.ino — ESP32 + SX1262 scanning gateway. Prints CAP CSV for measure.py */
#include "poc_node.h"
#include "radio_hal.h"

#define SLOT_MS 100
#define SCHEME_LABEL "chaos"
static const uint8_t SEED[] = "FORGE-mesh-seed-01";
static const uint8_t KEY[16] = "pair-key-16bytes";

poc_t gw;

void setup() {
    Serial.begin(115200);
    hal_init();
    poc_init(&gw, POC_ROLE_GW, SEED, sizeof(SEED) - 1, KEY);
    Serial.println("# CAP rows: CAP,scheme,slot,ch,rssi,crc_ok,lat_slots");
}

void loop() {
    static uint32_t last = 0, last_rs = 0;
    uint32_t now = millis();
    if (now - last >= SLOT_MS) {
        last = now;
        uint32_t exp = gw.slot, rs = 0;
        uint8_t pl[POC_PLEN], rc = 0;
        uint32_t rs0 = gw.resyncs;
        int got = poc_gw_tick(&gw, pl, &rs, &rc);
        if (gw.resyncs != rs0) {
            Serial.print("RESYNC,");
            Serial.print(SCHEME_LABEL);
            Serial.print(",");
            Serial.println(rs);
        }
        if (got) {
            Serial.print("CAP,");
            Serial.print(SCHEME_LABEL);
            Serial.print(",");
            Serial.print(rs);
            Serial.print(",");
            Serial.print(rc);
            Serial.print(",");
            Serial.print(hal_rssi());
            Serial.print(",1,");
            Serial.println(exp >= rs ? exp - rs : 0);
            last_rs = rs;
        }
        (void)last_rs;
    }
}
