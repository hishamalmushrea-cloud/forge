#!/usr/bin/env node
/* Runtime tests for whisper core (same selfTest() the browser button runs). */
import { selfTest } from './core.js';

const T = await selfTest();
let fail = 0;
for (const t of T) {
    console.log((t.pass ? 'PASS' : 'FAIL'), t.name, '-', t.detail);
    if (!t.pass) fail++;
}
console.log(fail ? 'WHISPER CORE: FAIL' : `WHISPER CORE: ALL ${T.length} PASS`);
process.exit(fail ? 1 : 0);
