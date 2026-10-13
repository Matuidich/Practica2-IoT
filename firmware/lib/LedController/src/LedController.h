#pragma once
#include <stdint.h>
#include "ProtocolCodec.h"

class LedController {
public:
    LedController(int red, int yellow, int green);
    void begin();
    void apply(const Protocol::Message& command, uint32_t now);
    void update(uint32_t now);
    void off(uint32_t now);
private:
    struct Channel {
        int pin;
        Protocol::LedMode mode = Protocol::LedMode::Off;
        bool high = false;
        uint32_t changedAt = 0;
    };
    static void setMode(Channel& channel, Protocol::LedMode mode, uint32_t now);
    Channel channels_[3];
};
