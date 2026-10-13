#include "ProtocolCodec.h"
#include "LedController.h"
#include "UltrasonicSensor.h"
#include "Arduino.h"
#include <cassert>
#include <cmath>
#include <iostream>
#include <map>
#include <string>

namespace {
std::map<int, int> outputs;
std::map<int, int> modes;
unsigned long echoDuration = 0;
}

void pinMode(int pin, int mode) { modes[pin] = mode; }
void digitalWrite(int pin, int value) { outputs[pin] = value; }
void delayMicroseconds(unsigned int) {}
unsigned long pulseIn(int, int, unsigned long) { return echoDuration; }

void selfTest() {
    Protocol::LineBuffer buffer;
    std::string messages[] = {"REGISTER type=sensor", "POST distance=20", "POST status=invalid"};
    size_t ready = 0;
    for (char c : std::string("REGISTER type=sensor\r\nPOST distance=20\nPOST status=invalid\n")) {
        auto result = buffer.push(c);
        if (result == Protocol::LineBuffer::Result::Ready) { assert(messages[ready++] == buffer.line()); }
        else { assert(result == Protocol::LineBuffer::Result::Pending); }
    }
    assert(ready == 3);
    for (size_t i = 0; i < 256; ++i) { assert(buffer.push('x') == Protocol::LineBuffer::Result::Pending); }
    assert(buffer.push('\r') == Protocol::LineBuffer::Result::Pending);
    assert(buffer.push('\n') == Protocol::LineBuffer::Result::Ready);
    assert(std::string(buffer.line()).size() == 256);
    for (size_t i = 0; i < 256; ++i) { buffer.push('x'); }
    assert(buffer.push('x') == Protocol::LineBuffer::Result::Error);

    LedController leds(25, 26, 27);
    leds.begin();
    assert(outputs[25] == LOW && outputs[26] == LOW && outputs[27] == LOW);
    Protocol::Message command;
    assert(Protocol::ProtocolCodec::parse("SET redLed=blink_4, yellowLed=off, greenLed=off", command));
    leds.apply(command, 0);
    assert(outputs[25] == HIGH);
    leds.update(124); assert(outputs[25] == HIGH);
    leds.update(125); assert(outputs[25] == LOW);
    leds.apply(command, 180);
    leds.update(249); assert(outputs[25] == LOW);
    leds.update(250); assert(outputs[25] == HIGH);
    leds.update(625); assert(outputs[25] == LOW);
    leds.off(630); assert(outputs[25] == LOW);
    assert(Protocol::ProtocolCodec::parse("SET redLed=off yellowLed=blink_2 greenLed=off", command));
    leds.apply(command, 700);
    leds.update(949); assert(outputs[26] == HIGH);
    leds.update(950); assert(outputs[26] == LOW);
    leds.off(1000);
    command.yellow = Protocol::LedMode::Off;
    command.red = Protocol::LedMode::Blink4;
    leds.apply(command, UINT32_MAX - 100U);
    leds.update(24U); assert(outputs[25] == LOW);
    leds.update(149U); assert(outputs[25] == HIGH);
    leds.off(150U); assert(outputs[25] == LOW);

    UltrasonicSensor sensor(5, 18);
    sensor.begin();
    assert(modes[5] == OUTPUT && modes[18] == INPUT && outputs[5] == LOW);
    float distance = 0;
    assert(!sensor.getDistance().distanceCm(distance));
    echoDuration = 1000;
    assert(sensor.getDistance().distanceCm(distance));
    assert(std::abs(distance - 17.0f) < 0.001f);
    assert(!UltrasonicSensor::Measurement::valid(NAN).isValid());
    assert(!UltrasonicSensor::Measurement::valid(-1).isValid());
    std::cout << "Native framing, LED timing, rollover and ultrasonic tests passed\n";
}

int main(int argc, char**) {
    if (argc > 1) { selfTest(); return 0; }
    std::string line;
    while (std::getline(std::cin, line)) {
        if (!line.empty() && line.back() == '\r') { line.pop_back(); }
        Protocol::Message message;
        if (Protocol::ProtocolCodec::parse(line.c_str(), message)) {
            std::cout << "OK " << Protocol::ProtocolCodec::kindName(message.kind) << '\n';
        } else { std::cout << "ERROR " << message.errorCode << '\n'; }
    }
}
