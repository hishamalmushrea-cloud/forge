#!/usr/bin/env python3
"""PoC TX: hop-transmit packets per --scheme. REQUIRES: gnuradio + gr-osmosdr + TX SDR.
Usage: tx.py --scheme chaos --gain 20 --slot-ms 100 --nslots 2000"""
import argparse
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from pktutil import build, gen_scheme, CH_FREQ  # noqa: E402

try:
    from gnuradio import gr, blocks, digital, osmosdr
except ImportError:
    sys.exit('needs GNU Radio + gr-osmosdr. See poc/test_procedure.md phase 3.')

KEY = b'pair-key-16bytes'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scheme', default='chaos', choices=['fixed', 'lfsr', 'hash', 'chaos'])
    ap.add_argument('--gain', type=float, default=20)
    ap.add_argument('--slot-ms', type=float, default=100)
    ap.add_argument('--nslots', type=int, default=2000)
    a = ap.parse_args()
    hops = gen_scheme(a.scheme, a.nslots)
    tb = gr.top_block()
    src = blocks.vector_source_b([], False)
    mod = digital.gmsk_mod(samples_per_symbol=2, bt=0.35, verbose=False, log=False)
    snk = osmosdr.sink('numchan=1')
    snk.set_sample_rate(1e6)
    snk.set_gain(a.gain)
    tb.connect(src, mod, snk)
    tb.start()
    for t, ch in enumerate(hops):
        snk.set_center_freq(CH_FREQ[ch] * 1e6)
        src.set_data(list(build(t, bytes([t & 0xFF]) * 8, KEY)))
        time.sleep(a.slot_ms / 1000.0)
    tb.stop()
    tb.wait()
    print(f'TX done: {a.nslots} slots scheme={a.scheme}')


if __name__ == '__main__':
    main()
