// MUSHREA FORGE — Electrolyzer logger v0.2 (measurement subsystem fixed)
// STATUS: WRITTEN, STATIC-REVIEWED, NOT EXECUTED on hardware (no HW in sandbox)
// FIX v0.2: standard INA219 (max ~3.2A) CANNOT measure 4A -> replaced by:
//   - ACS712-20A Hall current sensor on A1 (100 mV/A, zero ~2.5V)
//   - Voltage divider 10k/10k on A0 (cell V, up to ~10V range)
//   - Relay module (ACTIVE-LOW) on D9 in PSU line for trip cutoff
// CALIBRATE BEFORE USE: (1) power Arduino with NO cell current, read A1 -> set ACS_ZERO;
// (2) verify divider against a multimeter at ~2V -> adjust DIV_RATIO if needed.
#define PIN_VCELL A0
#define PIN_CURR A1
#define CUT_PIN 9
#define VREF 5.0
#define DIV_RATIO 2.0        // (10k+10k)/10k
#define ACS_ZERO 512.0       // ADC counts at 0A -> CALIBRATE
#define ACS_MV_PER_A 100.0
#define I_TRIP_A 5.0
#define T_MAX_S 7200UL
const float F_CONST = 96485.0;
double coulombs = 0;
unsigned long t0, last;
float readAvg(int pin) {
  long sum = 0;
  for (int k = 0; k < 50; k++) { sum += analogRead(pin); delay(2); }
  return sum / 50.0;
}
void setup() {
  Serial.begin(9600);
  pinMode(CUT_PIN, OUTPUT); digitalWrite(CUT_PIN, LOW); // relay ON (active-low)
  t0 = last = millis();
  Serial.println("t_s,Vcell_V,ImA,coulombs,H2_pred_mL,relay");
}
void loop() {
  unsigned long now = millis();
  float dt = (now - last) / 1000.0; last = now;
  float vcell = readAvg(PIN_VCELL) * VREF / 1023.0 * DIV_RATIO;
  float iamp = ((readAvg(PIN_CURR) * VREF / 1023.0 * 1000.0) - (ACS_ZERO * VREF / 1023.0 * 1000.0)) / ACS_MV_PER_A;
  coulombs += iamp * dt;
  double h2ml = coulombs / (2.0 * F_CONST) * 24450.0;
  bool trip = (iamp > I_TRIP_A) || ((now - t0) / 1000UL > T_MAX_S);
  digitalWrite(CUT_PIN, trip ? HIGH : LOW);
  Serial.print((now - t0) / 1000); Serial.print(","); Serial.print(vcell, 3); Serial.print(",");
  Serial.print(iamp * 1000.0, 1); Serial.print(","); Serial.print(coulombs, 1); Serial.print(",");
  Serial.print(h2ml, 1); Serial.print(","); Serial.println(trip ? 0 : 1);
  delay(1000);
}
