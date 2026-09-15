/* Host test: golden-hop match (bit-exactness) + SHA-256/HMAC vectors + avalanche. */
#include <stdio.h>
#include <string.h>
#include "hop.h"
#include "sha256.h"
#include "golden.h"

static int fails = 0;
#define CHECK(c, ...) do { \
    if (c) { printf("PASS "); printf(__VA_ARGS__); printf("\n"); } \
    else { printf("FAIL "); printf(__VA_ARGS__); printf("\n"); fails++; } } while (0)

static void hexout(const uint8_t *b, char *o) {
    for (int i = 0; i < 32; i++) sprintf(o + 2 * i, "%02x", b[i]);
}

int main(void) {
    /* T1b: firmware hops vs python oracle */
    mesh_state_t s;
    mesh_seed(&s, (const uint8_t *)"FORGE-mesh-seed-01", 18);
    int match = 0;
    for (int i = 0; i < NHOP; i++)
        if (mesh_next(&s) == GOLDEN[i]) match++;
    CHECK(match == NHOP, "T1b golden-match %d/%d", match, NHOP);

    /* T4b: SHA-256('abc') FIPS vector */
    uint8_t d[32];
    char hx[65];
    sha256((const uint8_t *)"abc", 3, d);
    hexout(d, hx);
    CHECK(!strcmp(hx, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),
          "T4b sha256-abc %s", hx);

    /* T4c: RFC 4237 Test 1 HMAC-SHA-256 */
    uint8_t key[20];
    memset(key, 0x0b, 20);
    hmac_sha256(key, 20, (const uint8_t *)"Hi There", 8, d);
    hexout(d, hx);
    CHECK(!strcmp(hx, "b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7"),
          "T4c rfc4237 %s", hx);

    /* T4d: avalanche in firmware (seed flip => hops differ >= 40%) */
    mesh_state_t a, b;
    mesh_seed(&a, (const uint8_t *)"FORGE-mesh-seed-01", 18);
    mesh_seed(&b, (const uint8_t *)"FORGE-mesh-seed-02", 18);
    int diff = 0;
    for (int i = 0; i < NHOP; i++)
        if (mesh_next(&a) != mesh_next(&b)) diff++;
    CHECK(diff >= (int)(0.40 * NHOP), "T4d avalanche %d/%d", diff, NHOP);

    printf(fails ? "HOST TESTS: FAIL\n" : "HOST TESTS: ALL PASS\n");
    return fails ? 1 : 0;
}
