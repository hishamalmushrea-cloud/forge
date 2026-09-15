// whisper core — environment-agnostic (browser + Node 22). No DOM. ESM.
const subtle = globalThis.crypto.subtle;
const rnd = (n) => globalThis.crypto.getRandomValues(new Uint8Array(n));

export const WORDS = ["نجم","قمر","شمس","جبل","نهر","بحر","برق","رعد","غيم","مطر",
"فجر","ليل","صقر","حصان","سفينة","سيف","حصن","وردة","عسل","تمر","بن","زهرة",
"قوس","رمح","خيمة","بئر","واحة","نخلة","عاصفة","نسيم","شعلة","مرجان"];
export const GRID = 45, FRAME_PAYLOAD = 225, SOUND_MAX = 300;

// ---------- CRC16 ----------
export function crc16(d) {
    let c = 0xFFFF;
    for (const b of d) {
        c ^= b << 8;
        for (let k = 0; k < 8; k++) c = (c & 0x8000) ? ((c << 1) ^ 0x1021) & 0xFFFF : (c << 1) & 0xFFFF;
    }
    return c;
}

// ---------- P-256 compress / decompress ----------
const P = 2n**256n - 2n**224n + 2n**192n + 2n**96n - 1n;
const B256 = 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604bn;
function powMod(a, e) { let r = 1n; a %= P; while (e) { if (e & 1n) r = (r * a) % P; a = (a * a) % P; e >>= 1n; } return r; }
const bi = (u8) => BigInt('0x' + [...u8].map(b => b.toString(16).padStart(2, '0')).join(''));
function unbi(x) { const h = x.toString(16).padStart(64, '0'); return Uint8Array.from(h.match(/../g).map(s => parseInt(s, 16))); }

export function compressPub(raw65) {
    if (raw65[0] !== 0x04 || raw65.length !== 65) throw new Error('bad raw pubkey');
    const out = new Uint8Array(33);
    out[0] = (raw65[64] & 1) ? 0x03 : 0x02;
    out.set(raw65.slice(1, 33), 1);
    return out;
}
export function decompressPub(c33) {
    if ((c33[0] !== 0x02 && c33[0] !== 0x03) || c33.length !== 33) throw new Error('bad compressed');
    const x = bi(c33.slice(1));
    const rhs = (powMod(x, 3n) - 3n * x + B256) % P;
    let y = powMod(rhs, (P + 1n) / 4n);
    if ((y * y) % P !== (rhs + P) % P) throw new Error('not on curve');
    if (Number(y & 1n) !== (c33[0] - 0x02)) y = P - y;
    const out = new Uint8Array(65);
    out[0] = 0x04; out.set(unbi(x), 1); out.set(unbi(y), 33);
    return out;
}

// ---------- identity / fingerprint ----------
export async function genIdentity() {
    const kp = await subtle.generateKey({ name: 'ECDH', namedCurve: 'P-256' }, true, ['deriveBits']);
    const raw = new Uint8Array(await subtle.exportKey('raw', kp.publicKey));
    return { priv: kp.privateKey, raw, comp: compressPub(raw) };
}
export async function fingerprint(comp33) {
    const d = new Uint8Array(await subtle.digest('SHA-256', comp33));
    const words = [];
    let acc = 0, bits = 0;
    for (const b of d) {
        acc = (acc << 8) | b; bits += 8;
        while (bits >= 5 && words.length < 12) { bits -= 5; words.push(WORDS[(acc >> bits) & 31]); }
    }
    return words;
}

// ---------- capsule seal / open ----------
async function aesKey(shared32, salt16) {
    const hk = await subtle.importKey('raw', shared32, 'HKDF', false, ['deriveBits']);
    const kb = await subtle.deriveBits({ name: 'HKDF', hash: 'SHA-256', salt: salt16, info: new TextEncoder().encode('whisper-v1') }, hk, 256);
    return subtle.importKey('raw', kb, 'AES-GCM', false, ['encrypt', 'decrypt']);
}
export async function seal(senderPriv, senderComp, recipRaw65, plaintext) {
    const eph = await genIdentity();
    const recipPub = await subtle.importKey('raw', recipRaw65, { name: 'ECDH', namedCurve: 'P-256' }, true, []);
    const shared = new Uint8Array(await subtle.deriveBits({ name: 'ECDH', public: recipPub }, eph.priv, 256));
    const salt = rnd(16), nonce = rnd(12);
    const key = await aesKey(shared, salt);
    const ct = new Uint8Array(await subtle.encrypt({ name: 'AES-GCM', iv: nonce, additionalData: senderComp }, key, plaintext));
    const out = new Uint8Array(1 + 33 + 16 + 12 + ct.length);
    out[0] = 0x01; out.set(eph.comp, 1); out.set(salt, 34); out.set(nonce, 50); out.set(ct, 62);
    return out;
}
export async function open(recipPriv, capsule, expectedSenderComp) {
    if (capsule[0] !== 0x01 || capsule.length < 62 + 16) throw new Error('bad capsule');
    const ephRaw = decompressPub(capsule.slice(1, 34));
    const ephPub = await subtle.importKey('raw', ephRaw, { name: 'ECDH', namedCurve: 'P-256' }, true, []);
    const shared = new Uint8Array(await subtle.deriveBits({ name: 'ECDH', public: ephPub }, recipPriv, 256));
    const key = await aesKey(shared, capsule.slice(34, 50));
    const pt = await subtle.decrypt({ name: 'AES-GCM', iv: capsule.slice(50, 62), additionalData: expectedSenderComp || new Uint8Array(0) }, key, capsule.slice(62));
    return new Uint8Array(pt);
}

// ---------- frame code (45x45, finder corners, CRC, multi-frame) ----------
const FINDERS = [[0, 0], [GRID - 7, 0], [0, GRID - 7]];
const inFinder = (x, y) => FINDERS.some(([fx, fy]) => x >= fx && x < fx + 7 && y >= fy && y < fy + 7);
function dataCells() {
    const cells = [];
    for (let y = 0; y < GRID; y++) for (let x = 0; x < GRID; x++) if (!inFinder(x, y)) cells.push([x, y]);
    return cells;
}
const CELLS = dataCells(); // 1878 bits = 234 bytes
function bytesToBits(u8) { const o = []; for (const b of u8) for (let k = 7; k >= 0; k--) o.push((b >> k) & 1); return o; }
function bitsToBytes(bits) {
    const o = new Uint8Array(bits.length / 8);
    for (let i = 0; i < o.length; i++) { let b = 0; for (let k = 0; k < 8; k++) b = (b << 1) | bits[i * 8 + k]; o[i] = b; }
    return o;
}
export function encodeFrames(data) {
    const frames = [];
    const total = Math.ceil(data.length / FRAME_PAYLOAD);
    for (let idx = 0; idx < total; idx++) {
        const pl = data.slice(idx * FRAME_PAYLOAD, (idx + 1) * FRAME_PAYLOAD);
        const f = new Uint8Array(9 + pl.length);
        f[0] = 0x48; f[1] = 0x4D; f[2] = 0; f[3] = total; f[4] = idx;
        f[5] = pl.length & 0xFF; f[6] = (pl.length >> 8) & 0xFF;
        f.set(pl, 7);
        const c = crc16(f.slice(0, 7 + pl.length));
        f[7 + pl.length] = c >> 8; f[8 + pl.length] = c & 0xFF;
        const bits = bytesToBits(f);
        const grid = new Uint8Array(GRID * GRID);
        bits.forEach((b, i) => { const [x, y] = CELLS[i]; grid[y * GRID + x] = b; });
        frames.push(grid);
    }
    return frames;
}
export function decodeFrame(grid) {
    const bits = CELLS.map(([x, y]) => grid[y * GRID + x]);
    const raw = bitsToBytes(bits.slice(0, Math.floor(bits.length / 8) * 8));
    if (raw[0] !== 0x48 || raw[1] !== 0x4D) throw new Error('bad magic');
    const total = raw[3], idx = raw[4], len = raw[5] | (raw[6] << 8);
    if (idx >= total || len > FRAME_PAYLOAD) throw new Error('bad header');
    const c = crc16(raw.slice(0, 7 + len));
    if (((c >> 8) & 0xFF) !== raw[7 + len] || (c & 0xFF) !== raw[8 + len]) throw new Error('CRC fail');
    return { total, idx, payload: raw.slice(7, 7 + len) };
}
export function decodeFrames(grids) {
    const got = new Map();
    for (const g of grids) { try { const f = decodeFrame(g); if (!got.has(f.idx)) got.set(f.idx, f); } catch { /* skip bad */ } }
    if (!got.size) throw new Error('no valid frames');
    const total = [...got.values()][0].total;
    for (const f of got.values()) if (f.total !== total) throw new Error('mixed message');
    if (got.size !== total) throw new Error(`missing frames ${got.size}/${total}`);
    const parts = [...got.entries()].sort((a, b) => a[0] - b[0]).map(([, f]) => f.payload);
    const out = new Uint8Array(parts.reduce((n, p) => n + p.length, 0));
    let o = 0;
    for (const p of parts) { out.set(p, o); o += p.length; }
    return out;
}

// ---------- ultrasonic FSK (18/19 kHz, 100 baud) ----------
export const FSK = { sr: 48000, f0: 18000, f1: 19000, baud: 100 };
const SYNCW = [1,0,1,1,0,1,0,0,1,0,1,1,0,0,1,0]; // 0x2DD4-ish
export function fskMod(data) {
    if (data.length > SOUND_MAX) throw new Error('too long for sound, use visual/file');
    const bits = [];
    for (let i = 0; i < 20; i++) bits.push(i % 2);
    bits.push(...SYNCW);
    const len = data.length;
    for (let k = 15; k >= 0; k--) bits.push((len >> k) & 1);
    bits.push(...bytesToBits(data));
    const c = crc16(data);
    for (let k = 15; k >= 0; k--) bits.push((c >> k) & 1);
    const { sr, f0, f1, baud } = FSK, sps = Math.round(sr / baud), out = new Float32Array(bits.length * sps);
    let ph = 0, o = 0;
    for (const b of bits) {
        const f = b ? f1 : f0;
        for (let i = 0; i < sps; i++) { out[o++] = Math.cos(ph); ph += 2 * Math.PI * f / sr; }
    }
    return { samples: out, seconds: +(out.length / sr).toFixed(1) };
}
function goertzel(s, off, n, f, sr) {
    const w = 2 * Math.PI * f / sr, cw = Math.cos(w);
    let s0 = 0, s1 = 0, s2 = 0;
    for (let i = 0; i < n; i++) { s0 = s[off + i] + 2 * cw * s1 - s2; s2 = s1; s1 = s0; }
    return s1 * s1 + s2 * s2 - 2 * cw * s1 * s2;
}
export function addNoise(s, snrDb, seed = 7) {
    let st = seed;
    const rndn = () => (st = (st * 1103515245 + 12345) & 0x7fffffff) / 0x40000000 - 1;
    let e = 0;
    for (const v of s) e += v * v;
    const sigma = Math.sqrt(e / s.length / Math.pow(10, snrDb / 10));
    return Float32Array.from(s, (v) => v + (rndn() + rndn() + rndn()) * 0.577 * sigma);
}
export function fskDemod(s) {
    const { sr, f0, f1, baud } = FSK, sps = Math.round(sr / baud);
    let start = 0;
    while (start < s.length - sps && Math.abs(s[start]) < 0.05) start++;
    const bits = [];
    for (let o = start; o + sps <= s.length; o += sps)
        bits.push(goertzel(s, o, sps, f1, sr) > goertzel(s, o, sps, f0, sr) ? 1 : 0);
    const idx = (() => {
        outer: for (let i = 0; i + SYNCW.length <= bits.length; i++) {
            for (let j = 0; j < SYNCW.length; j++) if (bits[i + j] !== SYNCW[j]) continue outer;
            return i + SYNCW.length;
        }
        return -1;
    })();
    if (idx < 0) throw new Error('no sync');
    let len = 0;
    for (let k = 0; k < 16; k++) len = (len << 1) | bits[idx + k];
    if (len > SOUND_MAX) throw new Error('bad len');
    const pbits = bits.slice(idx + 16, idx + 16 + len * 8);
    if (pbits.length < len * 8) throw new Error('truncated');
    const data = bitsToBytes(pbits);
    let c = 0;
    for (let k = 0; k < 16; k++) c = (c << 1) | bits[idx + 16 + len * 8 + k];
    if (c !== crc16(data)) throw new Error('CRC fail');
    return data;
}

// ---------- self-test (Node + browser button share this) ----------
export async function selfTest() {
    const T = [];
    const t = async (name, fn) => {
        try { T.push({ name, pass: true, detail: await fn() }); }
        catch (e) { T.push({ name, pass: false, detail: String(e.message || e) }); }
    };
    await t('words-32-unique', async () => {
        if (WORDS.length !== 32 || new Set(WORDS).size !== 32) throw new Error('wordlist');
        return '32/32';
    });
    const A = await genIdentity(), B = await genIdentity();
    await t('ec-compress-roundtrip', async () => {
        const r = decompressPub(compressPub(A.raw));
        if (r.join() !== A.raw.join()) throw new Error('mismatch');
        return '65B ok';
    });
    await t('ecdh-agree', async () => {
        const [pa, pb] = await Promise.all([A, B].map(async (I) =>
            subtle.importKey('raw', I.raw, { name: 'ECDH', namedCurve: 'P-256' }, true, [])));
        const sa = new Uint8Array(await subtle.deriveBits({ name: 'ECDH', public: pb }, A.priv, 256));
        const sb = new Uint8Array(await subtle.deriveBits({ name: 'ECDH', public: pa }, B.priv, 256));
        if (sa.join() !== sb.join()) throw new Error('shared differ');
        return '256-bit match';
    });
    const MSG = new TextEncoder().encode('صباح الخير يا تعز! هذه رسالة همس مشفرة تسبق التقنية.');
    const CAP = await seal(A.priv, A.comp, B.raw, MSG);
    await t('capsule-size-single-frame', async () => {
        if (CAP.length > FRAME_PAYLOAD) throw new Error(`${CAP.length}B > 1 frame`);
        return `${CAP.length}B = 1 frame`;
    });
    await t('seal-open-roundtrip', async () => {
        const pt = await open(B.priv, CAP, A.comp);
        if (new TextDecoder().decode(pt) !== new TextDecoder().decode(MSG)) throw new Error('text differ');
        return `${MSG.length}B ok`;
    });
    await t('tamper-reject', async () => {
        const bad = CAP.slice(); bad[bad.length - 1] ^= 1;
        try { await open(B.priv, bad, A.comp); throw new Error('accepted forged!'); }
        catch (e) { if (/forged/.test(e.message)) throw e; return 'GCM rejected'; }
    });
    await t('wrong-sender-reject', async () => {
        try { await open(B.priv, CAP, B.comp); throw new Error('accepted wrong AAD!'); }
        catch (e) { if (/AAD/.test(e.message)) throw e; return 'AAD rejected'; }
    });
    await t('fingerprint-12-words', async () => {
        const w = await fingerprint(A.comp);
        if (w.length !== 12) throw new Error('not 12');
        return w.slice(0, 3).join('،') + '…';
    });
    await t('frames-500B-3way', async () => {
        const d = rnd(500);
        const fr = encodeFrames(d);
        if (fr.length !== 3) throw new Error(`${fr.length} frames`);
        const back = decodeFrames([...fr].reverse());
        if (back.join() !== d.join()) throw new Error('mismatch');
        return '3 frames, order-free';
    });
    await t('frames-crc-reject', async () => {
        const fr = encodeFrames(rnd(100));
        fr[0][100] ^= 1;
        try { decodeFrames(fr); throw new Error('accepted corrupt!'); }
        catch (e) { if (/corrupt/.test(e.message)) throw e; return 'CRC rejected'; }
    });
    await t('fsk-clean', async () => {
        const { samples, seconds } = fskMod(CAP);
        const back = fskDemod(samples);
        if (back.join() !== CAP.join()) throw new Error('mismatch');
        return `${seconds}s ok`;
    });
    await t('fsk-20dB', async () => {
        const back = fskDemod(addNoise(fskMod(CAP).samples, 20));
        if (back.join() !== CAP.join()) throw new Error('mismatch@20dB');
        return '+20dB ok';
    });
    const noisy = await (async () => {
        try { fskDemod(addNoise(fskMod(CAP).samples, 6)); return 'survived?!'; }
        catch { return 'fails (expected — v2 FEC)'; }
    })();
    T.push({ name: 'fsk-6dB-report', pass: true, detail: noisy });
    return T;
}
