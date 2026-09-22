/* mesh_poc_node.ino — ESP32 + SX1262 chaos-hop node (FSK 50kbps).
   Arduino IDE: copy common/* + radio_hal.h + hal_sx1262_radiolib.cpp here. Needs RadioLib. */
#include "poc_node.h"
#include "radio_hal.h"

#define SLOT_MS 100
static const uint8_t SEED[] = "FORGE-mesh-seed-01"; /* PoC: flash same both sides */
static const uint8_t KEY[16] = "pair-key-16bytes";

poc_t node;

void setup() {
    Serial.begin(115200);
    hal_init();
    poc_init(&node, POC_ROLE_NODE, SEED, sizeof(SEED) - 1, KEY);
    Serial.println("NODE ready");
}

void loop() {
    static uint32_t last = 0;
    uint32_t now = millis();
    if (now - last >= SLOT_MS) {
        last = now;
        uint8_t pl[POC_PLEN] = {0};
        pl[0] = (node.slot >> 8) & 0xFF;
        pl[1] = node.slot & 0xFF;
        poc_node_tick(&node, pl);
    }
}
