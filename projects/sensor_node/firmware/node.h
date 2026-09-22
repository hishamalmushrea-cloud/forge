#ifndef NODE_H
#define NODE_H
/* MUSHREA FORGE — sensor node energy-aware logic (platform-independent).
 * STATUS: COMPILED + UNIT-TESTED on host (gcc). HW port still NOT EXECUTED. */

typedef enum { ACT_SLEEP = 0, ACT_TX = 1 } node_action_t;

typedef struct {
    int booted;      /* first-boot gate latched once Vcap > 3.0V */
    int sleep_min;   /* adaptive sleep interval */
    int tx_count;
    int skip_count;
} node_state_t;

void node_init(node_state_t *s);
node_action_t node_decide(node_state_t *s, float vcap);
void node_on_tx_done(node_state_t *s, float vcap_after);

#endif
