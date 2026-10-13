#include "UltrasonicSensor.h"

#include <math.h>

UltrasonicSensor::Measurement::Measurement(bool valid, float distanceCm)
    : valid_(valid), distanceCm_(distanceCm) {
}

UltrasonicSensor::Measurement UltrasonicSensor::Measurement::valid(float distanceCm) {
    if (!isfinite(distanceCm) || distanceCm <= 0.0f) {
        return invalid();
    }

    return Measurement(true, distanceCm);
}

UltrasonicSensor::Measurement UltrasonicSensor::Measurement::invalid() {
    return Measurement(false, 0.0f);
}

bool UltrasonicSensor::Measurement::isValid() const {
    return valid_;
}

bool UltrasonicSensor::Measurement::distanceCm(float &distanceCm) const {
    if (!valid_) {
        return false;
    }

    distanceCm = distanceCm_;
    return true;
}

UltrasonicSensor::UltrasonicSensor(int trig, int echo) {
    trigPin = trig;
    echoPin = echo;
}

void UltrasonicSensor::begin() {
    pinMode(trigPin, OUTPUT);
    pinMode(echoPin, INPUT);
    digitalWrite(trigPin, LOW);
}

UltrasonicSensor::Measurement UltrasonicSensor::getDistance() {

    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);

    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);

    digitalWrite(trigPin, LOW);

    unsigned long duration = pulseIn(echoPin, HIGH, ECHO_TIMEOUT_US);

    if (duration == 0) {
        return Measurement::invalid();
    }

    float distance = duration * 0.034f / 2.0f;

    if (distance <= 0.0f) {
        return Measurement::invalid();
    }

    return Measurement::valid(distance);
}
