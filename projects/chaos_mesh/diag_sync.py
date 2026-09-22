#!/usr/bin/env python3
"""One-off diagnostic: which chaotic drive-response pair actually locks?"""
DT = 0.01


def rk4(s, f, d):
    a = f(s, d)
    b = f([v + 0.5 * DT * x for v, x in zip(s, a)], d)
    c = f([v + 0.5 * DT * x for v, x in zip(s, b)], d)
    e = f([v + DT * x for v, x in zip(s, c)], d)
    return [v + DT / 6 * (a[i] + 2 * b[i] + 2 * c[i] + e[i]) for i, v in enumerate(s)]


def trial(name, fdrive, fresp, n, probes=(2000, 5000, 10000, 20000)):
    d = [1.0, 1.0, 1.0]
    r = [20.0, -5.0, 40.0][:n]
    out = {}
    for i in range(1, 20001):
        d = rk4(d, fdrive, None)
        r = rk4(r, fresp, d)
        if i in probes:
            out[i] = sum(abs(x - y) for x, y in zip(d[3 - n:], r))
    print(name, {k: f'{v:.1e}' for k, v in out.items()})


S, R, B = 10.0, 28.0, 8 / 3
S2, R2, B2 = 16.0, 45.6, 4.0
RA, RB, RC = 0.2, 0.2, 5.7

lor_std = lambda s, d: [S * (s[1] - s[0]), s[0] * (R - s[2]) - s[1], s[0] * s[1] - B * s[2]]
lor_co = lambda s, d: [S2 * (s[1] - s[0]), s[0] * (R2 - s[2]) - s[1], s[0] * s[1] - B2 * s[2]]
ros = lambda s, d: [-s[1] - s[2], s[0] + RA * s[1], RB + s[2] * (s[0] - RC)]

trial('1 Lstd-xrepl ', lor_std, lambda s, d: [d[0] * (R - s[1]) - s[0], d[0] * s[0] - B * s[1]], 2)
trial('2 Lco-xrepl  ', lor_co, lambda s, d: [d[0] * (R2 - s[1]) - s[0], d[0] * s[0] - B2 * s[1]], 2)
trial('3 Ros-xcpl.5 ', ros, lambda s, d: [-s[1] - s[2] + 0.5 * (d[0] - s[0]), s[0] + RA * s[1], RB + s[2] * (s[0] - RC)], 3)
trial('4 Lstd-xcpl20', lor_std, lambda s, d: [S * (s[1] - s[0]) + 20 * (d[0] - s[0]), s[0] * (R - s[2]) - s[1], s[0] * s[1] - B * s[2]], 3)
trial('5 Lstd-ycpl10', lor_std, lambda s, d: [S * (s[1] - s[0]), s[0] * (R - s[2]) - s[1] + 10 * (d[1] - s[1]), s[0] * s[1] - B * s[2]], 3)
trial('6 Ros-ycpl1  ', ros, lambda s, d: [-s[1] - s[2], s[0] + RA * s[1] + 1.0 * (d[1] - s[1]), RB + s[2] * (s[0] - RC)], 3)
