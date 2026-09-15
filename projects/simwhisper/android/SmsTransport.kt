package org.forge.simwhisper

// UNCOMPILED HERE — build in Android Studio (minSdk 26). Ports sms_codec.py format.
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import android.telephony.SmsManager

const val WHISPER_PORT: Short = 8091
const val SEG_BODY = 135

fun crc8(d: ByteArray): Int {
    var c = 0
    for (b in d) {
        c = c xor (b.toInt() and 0xFF)
        repeat(8) { c = if (c and 0x80 != 0) ((c shl 1) xor 0x07) and 0xFF else (c shl 1) and 0xFF }
    }
    return c
}

fun smsEncode(cap: ByteArray, msgid: Int): List<ByteArray> {
    val n = (cap.size + SEG_BODY - 1) / SEG_BODY
    val c = crc8(cap)
    return (0 until n).map { i ->
        val body = cap.sliceArray(i * SEG_BODY until minOf((i + 1) * SEG_BODY, cap.size))
        byteArrayOf(0x02, msgid.toByte(), n.toByte(), i.toByte(), c.toByte()) + body
    }
}

fun smsDecode(segs: List<ByteArray>): ByteArray {
    require(segs.isNotEmpty()) { "empty" }
    val (v, mid, n, _, c) = segs[0].take(5).map { it.toInt() and 0xFF }
    val parts = mutableMapOf<Int, ByteArray>()
    for (s in segs) {
        val h = s.take(5).map { it.toInt() and 0xFF }
        require(s.size >= 5 && h[0] == v && h[1] == mid && h[2] == n && h[4] == c && h[3] < n) { "bad/mixed" }
        parts.putIfAbsent(h[3], s.sliceArray(5 until s.size))
    }
    require(parts.size == n) { "incomplete" }
    val out = (0 until n).fold(byteArrayOf()) { acc, i -> acc + parts.getValue(i) }
    require(crc8(out) == c) { "crc8 fail" }
    return out
}

fun sendWhisperSms(ctx: Context, dest: String, capsule: ByteArray, msgid: Int) {
    val sm = if (Build.VERSION.SDK_INT >= 31) ctx.getSystemService(SmsManager::class.java)
             else @Suppress("DEPRECATION") SmsManager.getDefault()
    val si = PendingIntent.getBroadcast(ctx, 0, Intent("SMS_SENT"),
        PendingIntent.FLAG_IMMUTABLE)
    for (seg in smsEncode(capsule, msgid))
        sm.sendDataMessage(dest, null, WHISPER_PORT, seg, si, null)
}
// Receive: manifest receiver (see manifest_snippet.xml) -> getMessagesFromIntent -> messageBody/messageBytes
// -> collect by (msgid) -> smsDecode -> Whisper open (port core.js seal/open via WebView or Tink port).
