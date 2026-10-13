#include "LedController.h"
#include <Arduino.h>

LedController::LedController(int red, int yellow, int green) : channels_{{red}, {yellow}, {green}} {}

void LedController::begin() {
    for (Channel& channel : channels_) {
        pinMode(channel.pin, OUTPUT);
        digitalWrite(channel.pin, LOW);
    }
}

void LedController::setMode(Channel& channel, Protocol::LedMode mode, uint32_t now) {
    // Repeated commands refresh the watchdog in the app, not the blink phase.
    if (channel.mode == mode) { return; }
    channel.mode = mode;
    channel.high = mode != Protocol::LedMode::Off;
    channel.changedAt = now;
    digitalWrite(channel.pin, channel.high ? HIGH : LOW);
}

void LedController::apply(const Protocol::Message& command, uint32_t now) {
    setMode(channels_[0], command.red, now);
    setMode(channels_[1], command.yellow, now);
    setMode(channels_[2], command.green, now);
}

void LedController::off(uint32_t now) {
    apply(Protocol::Message{}, now);
}

void LedController::update(uint32_t now) {
    for (Channel& channel : channels_) {
        uint32_t interval = channel.mode == Protocol::LedMode::Blink4 ? 125U
                          : channel.mode == Protocol::LedMode::Blink2 ? 250U : 0U;
        if (!interval) { continue; }
        uint32_t periods = (now - channel.changedAt) / interval;
        if (periods) {
            if (periods % 2U) { channel.high = !channel.high; }
            channel.changedAt += periods * interval;
            digitalWrite(channel.pin, channel.high ? HIGH : LOW);
        }
    }
}
