#include <Arduino.h>
#include "UltrasonicSensor.h"

#define TRIG_PIN 5
#define ECHO_PIN 18

#define RED_LED 25
#define YELLOW_LED 26
#define GREEN_LED 27

constexpr float NEAR_THRESHOLD_CM = 20.0f;
constexpr float FAR_THRESHOLD_CM = 40.0f;
static_assert(NEAR_THRESHOLD_CM < FAR_THRESHOLD_CM, "Distance thresholds must be ordered");

constexpr unsigned long RED_BLINK_ON_MS = 125UL;
constexpr unsigned long RED_BLINK_OFF_MS = 125UL;
constexpr unsigned long SERIAL_BAUD_RATE = 115200UL;

enum class DistanceState {
    Invalid,
    Near,
    Mid,
    Far
};

UltrasonicSensor sensor(TRIG_PIN, ECHO_PIN);

DistanceState classifyDistance(const UltrasonicSensor::Measurement &measurement, float &distance) {
    if (!measurement.distanceCm(distance)) {
        return DistanceState::Invalid;
    }

    if (distance < NEAR_THRESHOLD_CM) {
        return DistanceState::Near;
    }

    if (distance <= FAR_THRESHOLD_CM) {
        return DistanceState::Mid;
    }

    return DistanceState::Far;
}

const char *distanceStateName(DistanceState state) {
    switch (state) {
        case DistanceState::Near:
            return "Near";
        case DistanceState::Mid:
            return "Mid";
        case DistanceState::Far:
            return "Far";
        case DistanceState::Invalid:
        default:
            return "Invalid";
    }
}

void reportMeasurement(DistanceState state, float distance) {
    if (state == DistanceState::Invalid) {
        Serial.println("Invalid measurement");
        return;
    }

    Serial.print("Distance: ");
    Serial.print(distance);
    Serial.print(" cm, State: ");
    Serial.println(distanceStateName(state));
}

void setLedOutputs(bool redOn, bool yellowOn, bool greenOn) {
    digitalWrite(RED_LED, redOn ? HIGH : LOW);
    digitalWrite(YELLOW_LED, yellowOn ? HIGH : LOW);
    digitalWrite(GREEN_LED, greenOn ? HIGH : LOW);
}

void applyLedState(DistanceState state) {
    switch (state) {
        case DistanceState::Near:
            setLedOutputs(true, false, false);
            delay(RED_BLINK_ON_MS);
            setLedOutputs(false, false, false);
            delay(RED_BLINK_OFF_MS);
            break;

        case DistanceState::Mid:
            setLedOutputs(false, true, false);
            break;

        case DistanceState::Far:
            setLedOutputs(false, false, true);
            break;

        case DistanceState::Invalid:
        default:
            setLedOutputs(false, false, false);
            break;
    }
}

void setup() {
    Serial.begin(SERIAL_BAUD_RATE);

    pinMode(RED_LED, OUTPUT);
    pinMode(YELLOW_LED, OUTPUT);
    pinMode(GREEN_LED, OUTPUT);

    digitalWrite(RED_LED, HIGH);
    digitalWrite(YELLOW_LED, HIGH);
    digitalWrite(GREEN_LED, HIGH);
}
void loop() {
    UltrasonicSensor::Measurement measurement = sensor.getDistance();

    float distance = 0.0f;

    DistanceState state = classifyDistance(measurement, distance);

    reportMeasurement(state, distance);

    applyLedState(state);
}
