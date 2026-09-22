// MUSHREA FORGE — TEG demonstrator: measure + heater control + CSV log
// STATUS: WRITTEN, NOT EXECUTED (requires physical hardware — FORGE S35 honesty)
// HW: Arduino Nano/Uno, MAX6675+K-type (hot), DS18B20 (cold), INA219 (TEG V/I),
//     logic MOSFET on D9 driving 12V heaters. Safety: heater OFF if Thot>145 or sensor fail.
#include <SPI.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_INA219.h>
#include "max6675.h"

#define ONE_WIRE_BUS 2
#define HEATER_PIN 9
#define SETPOINT_C 137.0 // nominal dT=85 operating point (P~1.14W, Thot<140 gate)
#define HYST_C 4.0
#define TRIP_C 145.0

MAX6675 tcouple(6, 5, 4); // SCK, CS, SO
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature coldSens(&oneWire);
Adafruit_INA219 ina219;

void setup() {
  Serial.begin(9600);
  pinMode(HEATER_PIN, OUTPUT);
  digitalWrite(HEATER_PIN, LOW);
  coldSens.begin();
  ina219.begin();
  ina219.setCalibration_16V_400mA();
  Serial.println("t_s,Thot_C,Tcold_C,Vbus_V,ImA,PmW,heater");
}

void loop() {
  static unsigned long t0 = millis();
  double thot = tcouple.readCelsius();
  coldSens.requestTemperatures();
  float tcold = coldSens.getTempCByIndex(0);
  float v = ina219.getBusVoltage_V();
  float i = ina219.getCurrent_mA();
  float p = ina219.getPower_mW();

  bool sensorOK = !isnan(thot) && thot > 0 && tcold > -50 && tcold < 125;
  static bool heater = false;
  if (!sensorOK || thot > TRIP_C) heater = false;              // FAIL-SAFE
  else if (thot < SETPOINT_C - HYST_C) heater = true;
  else if (thot > SETPOINT_C + HYST_C) heater = false;
  digitalWrite(HEATER_PIN, heater ? HIGH : LOW);

  Serial.print((millis() - t0) / 1000); Serial.print(",");
  Serial.print(thot); Serial.print(","); Serial.print(tcold); Serial.print(",");
  Serial.print(v); Serial.print(","); Serial.print(i); Serial.print(",");
  Serial.print(p); Serial.print(","); Serial.println(heater ? 1 : 0);
  delay(1000);
}
