#!/usr/bin/env python3
"""Calibrated jammer: barrage / sweep (live TX) + follower-analyze (offline BM demo).
SAFETY: cabled/attenuated first; OTA only short-range low-gain per test_procedure.md."""
import argparse
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from pktutil import CH_FREQ  # noqa: E402


def bm(bits):
    C, B, L, m = [1], [1], 0, 1
    for n in range(len(bits)):
        d = bits[n]
        for i in range(1, L + 1):
            if i < len(C):
                d ^= C[i] & bits[n - i]
        if d == 0:
            m += 1
            continue
        T = C[:]
        need = len(B) + m
        if len(C) < need:
            C += [0] * (need - len(C))
        for i in range(len(B)):
            C[i + m] ^= B[i]
        if 2 * L <= n:
            L, B, m = n + 1 - L, T, 1
        else:
            m += 1
    return C, L


def follower_analyze(path):
    chs = []
    for row in csv.reader(open(path)):
        if row and row[0] == 'CAP':
            chs.append(int(row[3]))
    hist, hits, att = [], 0, 0
    for t, c in enumerate(chs):
        if len(hist) >= 66:
            Cc, Lc = bm(hist[-64:])
            h = hist[:]
            pr = []
            for _ in range(3):
                b = 0
                for i in range(1, Lc + 1):
                    b ^= Cc[i] & h[-i]
                h.append(b)
                pr.append(b)
            att += 1
            hits += ((pr[0] | pr[1] << 1 | pr[2] << 2) == c)
        hist += [c & 1, (c >> 1) & 1, (c >> 2) & 1]
    acc = hits / max(att, 1)
    print(f'follower-analyze: {len(chs)} slots, predict-acc={acc:.3f} '
          f'({"VULNERABLE (>0.5)" if acc > 0.5 else "resistant (~0.125)"})')
    return acc


def live(mask, gain, secs, sweep):
    try:
        from gnuradio import gr, analog, blocks, osmosdr
    except ImportError:
        sys.exit('needs GNU Radio + gr-osmosdr for live modes.')
    import time
    tb = gr.top_block()
    snk = osmosdr.sink('numchan=1')
    snk.set_sample_rate(2e6)
    snk.set_gain(gain)
    if sweep:
        n = analog.noise_source_c(analog.GR_GAUSSIAN, 1.0)
        tb.connect(n, snk)
        tb.start()
        t0 = time.time()
        while time.time() - t0 < secs:
            for ch in range(8):
                snk.set_center_freq(CH_FREQ[ch] * 1e6)
                time.sleep(0.05)
        tb.stop()
    else:
        add = blocks.add_cc()
        tb.connect(add, snk)
        snk.set_center_freq(433.8e6)
        for ch in mask:
            n = analog.noise_source_c(analog.GR_GAUSSIAN, 0.5)
            off = blocks.rotator_cc((CH_FREQ[ch] - 433.8) * 1e6 / 2e6 * 6.2831853)
            tb.connect(n, off, add)
        tb.start()
        time.sleep(secs)
        tb.stop()
    tb.wait()
    print('jam done')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', required=True, choices=['barrage', 'sweep', 'follower-analyze'])
    ap.add_argument('--channels', default='0,1,2,3')
    ap.add_argument('--gain', type=float, default=10)
    ap.add_argument('--secs', type=float, default=220)
    ap.add_argument('--captures', default='captures.csv')
    a = ap.parse_args()
    if a.mode == 'follower-analyze':
        follower_analyze(a.captures)
    else:
        live([int(x) for x in a.channels.split(',')], a.gain, a.secs, a.mode == 'sweep')


if __name__ == '__main__':
    main()
