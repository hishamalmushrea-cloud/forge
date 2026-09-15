#!/usr/bin/env python3
"""Assert ESP32 common/ engine is byte-identical to verified firmware/ (no drift)."""
import filecmp
import pathlib
import sys

POC = pathlib.Path(__file__).parent
ok = True
for f in ('hop.h', 'hop.c', 'sha256.h', 'sha256.c'):
    a, b = POC / 'firmware_esp32' / 'common' / f, POC.parent / 'firmware' / f
    same = a.exists() and filecmp.cmp(a, b, shallow=False)
    print(('OK  ' if same else 'DIFF'), f)
    ok &= same
print('SYNC CHECK:', 'PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
