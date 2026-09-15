#!/usr/bin/env python3
"""Decisive: Rössler x-coupled at gains k — err + HOP agreement + impostor."""
DT = 0.01
RA, RB, RC = 0.2, 0.2, 5.7


def rk4(s, f):
    a = f(s)
    b = f([v + 0.5 * DT * x for v, x in zip(s, a)])
    c = f([v + 0.5 * DT * x for v, x in zip(s, b)])
    e = f([v + DT * x for v, x in zip(s, c)])
    return [v + DT / 6 * (a[i] + 2 * b[i] + 2 * c[i] + e[i]) for i, v in enumerate(s)]


def hop(y):
    wing = 0 if y > 0 else 1
    return (wing * 4 + int(abs(y) / 3.0) % 4) % 8


for k in (0.5, 2.0, 5.0, 10.0):
    fdrv = lambda s: [-s[1] - s[2], s[0] + RA * s[1], RB + s[2] * (s[0] - RC)]
    d = [1.0, 1.0, 1.0]
    n = [20.0, -5.0, 40.0]
    m = [20.0, -5.0, 40.0]
    for _ in range(5000):
        d = rk4(d, fdrv)
        xd = d[0]
        n = rk4(n, lambda s: [-s[1] - s[2] + k * (xd - s[0]), s[0] + RA * s[1], RB + s[2] * (s[0] - RC)])
        m = rk4(m, lambda s: [-s[1] - s[2] + k * (xd - s[0]), s[0] + RA * s[1], RB + s[2] * (s[0] - RC - 0.01)])
    ag = im = 0
    for _ in range(2000):
        for _ in range(50):
            d = rk4(d, fdrv)
            xd = d[0]
            n = rk4(n, lambda s: [-s[1] - s[2] + k * (xd - s[0]), s[0] + RA * s[1], RB + s[2] * (s[0] - RC)])
            m = rk4(m, lambda s: [-s[1] - s[2] + k * (xd - s[0]), s[0] + RA * s[1], RB + s[2] * (s[0] - RC - 0.01)])
        ag += hop(d[1]) == hop(n[1])
        im += hop(d[1]) == hop(m[1])
    err = sum(abs(x - y) for x, y in zip(d, n))
    print(f'k={k:>4}: err={err:.2e} agree={ag/2000:.4f} impostor={im/2000:.4f}')
