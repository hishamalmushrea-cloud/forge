#include "node.h"

#define V_FIRST_BOOT 3.0f
#define V_TX_MIN     2.3f   /* raised from 2.2: TX from 2.2 dips cap to 1.96V < 2.0 floor (found by host test) */
#define V_RELAX      2.4f
#define SLEEP_NOM    30
#define SLEEP_MAX    240

void node_init(node_state_t *s) {
    s->booted = 0; s->sleep_min = SLEEP_NOM; s->tx_count = 0; s->skip_count = 0;
}

node_action_t node_decide(node_state_t *s, float vcap) {
    if (!s->booted) {
        if (vcap >= V_FIRST_BOOT) s->booted = 1;
        else { s->skip_count++; return ACT_SLEEP; }
    }
    if (vcap < V_TX_MIN) { s->skip_count++; return ACT_SLEEP; }
    return ACT_TX;
}

void node_on_tx_done(node_state_t *s, float vcap_after) {
    s->tx_count++;
    if (vcap_after < V_RELAX && s->sleep_min < SLEEP_MAX) s->sleep_min *= 2;
    else if (vcap_after >= V_FIRST_BOOT) s->sleep_min = SLEEP_NOM;
}
