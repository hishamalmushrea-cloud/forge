#pragma once
/* Compact SHA-256 + HMAC-SHA-256. Verified vs FIPS vectors + RFC 4237. */
#include <stdint.h>

void sha256(const uint8_t *msg, uint32_t len, uint8_t out[32]);
void hmac_sha256(const uint8_t *key, uint32_t klen,
                 const uint8_t *msg, uint32_t mlen, uint8_t out[32]);
