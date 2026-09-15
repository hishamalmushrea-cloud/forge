"""Packet utils for SDR scripts (stdlib only): format, CRC, HMAC, hop generators."""
import hashlib
import hmac

CH_FREQ = [433.1 + 0.2 * i for i in range(8)]
PLEN, MACLEN, PKTLEN = 8, 8, 20


def crc16(d, c=0xFFFF):
    for b in d:
        c ^= b << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) & 0xFFFF if c & 0x8000 else (c << 1) & 0xFFFF
    return c


def build(slot, payload: bytes, key: bytes) -> bytes:
    assert len(payload) == PLEN and len(key) == 16
    hdr = bytes([(slot >> 8) & 0xFF, slot & 0xFF]) + payload
    mac = hmac.new(key, hdr, hashlib.sha256).digest()[:MACLEN]
    pkt = hdr + mac
    c = crc16(pkt)
    return pkt + bytes([c >> 8, c & 0xFF])


def parse(pkt: bytes, key: bytes):
    if len(pkt) != PKTLEN:
        return None
    if crc16(pkt[:18]) != (pkt[18] << 8 | pkt[19]):
        return None
    if hmac.new(key, pkt[:10], hashlib.sha256).digest()[:MACLEN] != pkt[10:18]:
        return None
    return (pkt[0] << 8 | pkt[1], pkt[2:10])


# ---- hop generators (mirror linksim) ----
S = 1 << 16


def _fsh(v, n):
    return v >> n if v >= 0 else -(((-v) + (1 << n) - 1) >> n)


def gen_chaos(seed: bytes, n, warm=3000, dwell=50):
    u = int.from_bytes(hashlib.sha256(seed).digest()[:8], 'big')
    X, Y, Z = S + u % (40 * S), S + (u >> 3) % (40 * S), S + (u >> 5) % (40 * S)
    for _ in range(warm):
        X += _fsh(10 * (Y - X), 7)
        Y += _fsh(_fsh(X * (28 * S - Z), 16) - Y, 7)
        Z += _fsh(_fsh(X * Y, 16) - (8 * Z) // 3, 7)
    out = []
    for _ in range(n):
        for _ in range(dwell):
            X += _fsh(10 * (Y - X), 7)
            Y += _fsh(_fsh(X * (28 * S - Z), 16) - Y, 7)
            Z += _fsh(_fsh(X * Y, 16) - (8 * Z) // 3, 7)
        out.append(((0 if Y > 0 else 1) * 4 + (_fsh(abs(Z), 16) // 6) % 4) % 8)
    return out


def gen_lfsr(n, seed=0xACE1):
    s = seed
    out = []
    for _ in range(n):
        c = 0
        for b in range(3):
            c |= (s & 1) << b
            fb = ((s >> 0) & 1) ^ ((s >> 2) & 1) ^ ((s >> 3) & 1) ^ ((s >> 5) & 1)
            s = (s >> 1) | (fb << 15)
        out.append(c)
    return out


def gen_hash(seed: bytes, n):
    out = []
    for c in range(n):
        out.append(int.from_bytes(hashlib.sha256(seed + c.to_bytes(4, 'big')).digest()[:2], 'big') % 8)
    return out


def gen_scheme(scheme, n):
    if scheme == 'fixed':
        return [0] * n
    if scheme == 'lfsr':
        return gen_lfsr(n)
    if scheme == 'hash':
        return gen_hash(b'POC-hash-seed-01', n)
    if scheme == 'chaos':
        return gen_chaos(b'FORGE-mesh-seed-01', n)
    raise ValueError(scheme)
