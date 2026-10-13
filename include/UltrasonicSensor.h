#ifndef ULTRASONIC_SENSOR_H
#define ULTRASONIC_SENSOR_H

#include <Arduino.h>

class UltrasonicSensor {
private:
    int trigPin;
    int echoPin;
    static const unsigned long ECHO_TIMEOUT_US = 30000UL;

public:
    class Measurement {
    private:
        bool valid_;
        float distanceCm_;

        Measurement(bool valid, float distanceCm);

    public:
        static Measurement valid(float distanceCm);
        static Measurement invalid();

        bool isValid() const;
        bool distanceCm(float &distanceCm) const;
    };

    UltrasonicSensor(int trig, int echo);

    void begin();

    Measurement getDistance();
};

#endif
