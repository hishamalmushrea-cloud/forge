/* Host test harness v2: unit checks + 3 energy scenarios (fresh/aged/starved).
 * Build: gcc -Wall -Wextra -o test_host test_host.c node.c -lm
 * v2 fixes: V_TX_MIN=2.3 (post-TX dip stays >=2.0V); min-ever energy tracked. */
#include <stdio.h>
#include <math.h>
#include "node.h"

static int fails = 0;
#define ASSERT(c, msg) do { if (c) printf("PASS: %s\n", msg); \
    else { printf("FAIL: %s\n", msg); fails++; } } while (0)

static void scenario(const char *name, double p_harv, int hours, int mode) {
    node_state_t s; node_init(&s);
    const double C = 0.1, EB = 0.05, EMAX = 0.5 * C * 3.3 * 3.3, EMIN = 0.5 * C * 2.0 * 2.0;
    double E = EMAX, t = 0, min_tx_v = 99, min_ever = EMAX;
    const double T_END = hours * 3600.0;
    while (t < T_END) {
        double v = sqrt(2 * E / C);
        if (node_decide(&s, (float)v) == ACT_TX) {
            if (v < min_tx_v) min_tx_v = v;
            E -= EB;
            node_on_tx_done(&s, (float)sqrt(2 * E / C));
        }
        if (E < min_ever) min_ever = E;
        double dt = s.sleep_min * 60.0;
        E += (p_harv - 8e-6) * dt;
        if (E > EMAX) E = EMAX;
        t += dt;
    }
    printf("[%s] tx=%d skip=%d sleep=%dmin minTXv=%.2f minEverV=%.2f\n",
           name, s.tx_count, s.skip_count, s.sleep_min, min_tx_v, sqrt(2 * min_ever / C));
    ASSERT(min_tx_v >= 2.29, "never TX below 2.3V gate");
    ASSERT(min_ever >= EMIN * 0.999, "capacitor never under 2.0V (min-ever)");
    if (mode == 0) ASSERT(s.tx_count >= 90 && s.skip_count == 0, "fresh: full rate, no skips");
    if (mode == 1) ASSERT(s.tx_count < 90 && s.sleep_min > 30, "aged: adapts rate down, survives");
    if (mode == 2) ASSERT(s.skip_count > 0 && s.tx_count >= 3, "starved: skips but keeps a trickle of TX");
}

int main(void) {
    node_state_t s; node_init(&s);
    ASSERT(node_decide(&s, 2.5f) == ACT_SLEEP, "boot gate blocks TX at 2.5V");
    ASSERT(node_decide(&s, 3.1f) == ACT_TX, "boot latches at 3.1V");
    ASSERT(node_decide(&s, 2.25f) == ACT_SLEEP, "below 2.3V gate skips TX");
    node_on_tx_done(&s, 2.3f);
    ASSERT(s.sleep_min == 60, "post-TX sag doubles sleep");
    node_on_tx_done(&s, 3.2f);
    ASSERT(s.sleep_min == 30, "healthy Vcap restores nominal sleep");
    scenario("fresh-50uW-48h", 50e-6, 48, 0);
    scenario("aged-25uW-48h", 25e-6, 48, 1);
    scenario("starved-10uW-48h", 10e-6, 48, 2);
    printf(fails ? "HOST TESTS: %d FAILURES\n" : "HOST TESTS: ALL PASS [VERIFIED]\n", fails);
    return fails != 0;
}
