package org.forge.simwhisper

// UNCOMPILED HERE — build in Android Studio. Mirrors ring_code.py meanings.
import android.telephony.PhoneStateListener
import android.telephony.TelephonyManager

val RING_MEANINGS = mapOf(1 to "تمام ✓", 2 to "اتصل بي ضروري", 3 to "تعال/خطر")
const val RING_WINDOW_MS = 90_000L

class RingListener(
    private val known: (String) -> Boolean,
    private val onPattern: (String, Int, String) -> Unit,
) : PhoneStateListener() {
    private val rings = mutableMapOf<String, MutableList<Long>>()

    @Deprecated("use registerTelephonyCallback on S+")
    override fun onCallStateChanged(state: Int, number: String?) {
        if (state != TelephonyManager.CALL_STATE_RINGING || number.isNullOrEmpty()) return
        if (!known(number)) return
        val now = System.currentTimeMillis()
        val ts = rings.getOrPut(number) { mutableListOf() }
        ts.add(now)
        val windowed = ts.filter { now - it <= RING_WINDOW_MS }
        rings[number] = windowed.toMutableList()
        // fire on each ring with running count (debounce: only escalate 1->2->3)
        onPattern(number, windowed.size, RING_MEANINGS[windowed.size] ?: "نمط غير معروف")
    }
}
// NOTE: incoming number needs READ_PHONE_STATE (+READ_CALL_LOG on 10+).
// This is a side-load/F-Droid style feature; Play's call-log policy is hostile — see README.
