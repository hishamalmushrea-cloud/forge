#!/usr/bin/env python3
"""PoC scanning gateway: wideband RX (2MHz covers all 8 ch) + 8 GMSK paths -> captures.csv.
REQUIRES: gnuradio + gr-osmosdr + RX SDR. Usage: rx.py --scheme chaos --gain 30 --secs 220"""
import argparse
import csv
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from pktutil import parse, CH_FREQ  # noqa: E402

try:
    from gnuradio import gr, blocks, digital, filter, osmosdr
except ImportError:
    sys.exit('needs GNU Radio + gr-osmosdr. See poc/test_procedure.md phase 3.')

KEY = b'pair-key-16bytes'
CENTER = 433.8


class ParseSink(gr.sync_block):
    def __init__(self, ch, w):
        gr.sync_block.__init__(self, 'parse', [], [])
        self.ch, self.w, self.buf = ch, w, bytearray()

    def work(self, in_sig, out_sig):
        self.buf += bytes(in_sig[0])
        while len(self.buf) >= 20:
            r = parse(bytes(self.buf[:20]), KEY)
            if r:
                self.w.writerow(['CAP', SCHEME, r[0], self.ch, -70, 1, 0])
                del self.buf[:20]
            else:
                del self.buf[:1]
        return len(in_sig[0])


SCHEME = 'chaos'


def main():
    global SCHEME
    ap = argparse.ArgumentParser()
    ap.add_argument('--scheme', default='chaos')
    ap.add_argument('--gain', type=float, default=30)
    ap.add_argument('--secs', type=float, default=220)
    ap.add_argument('--out', default='captures.csv')
    a = ap.parse_args()
    SCHEME = a.scheme
    tb = gr.top_block()
    src = osmosdr.source('numchan=1')
    src.set_sample_rate(2e6)
    src.set_center_freq(CENTER * 1e6)
    src.set_gain(a.gain)
    f = open(a.out, 'a', newline='')
    w = csv.writer(f)
    taps = filter.firdes.low_pass(1, 2e6, 100e3, 50e3)
    for ch in range(8):
        xl = filter.freq_xlating_fir_filter_ccc(4, taps, (CH_FREQ[ch] - CENTER) * 1e6, 2e6)
        dm = digital.gmsk_demod(samples_per_symbol=2, verbose=False, log=False)
        sk = ParseSink(ch, w)
        tb.connect(src, xl, dm, blocks.char_to_float(1), blocks.float_to_uchar(1), sk)
    tb.start()
    time.sleep(a.secs)
    tb.stop()
    tb.wait()
    f.close()
    print(f'RX done -> {a.out}')


if __name__ == '__main__':
    main()
