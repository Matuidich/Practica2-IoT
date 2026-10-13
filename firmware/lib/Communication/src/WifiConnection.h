#pragma once
#include <Arduino.h>

class WifiConnection {
public:
    void begin(const char* ssid, const char* password);
    bool update(uint32_t now);
private:
    const char* ssid_ = nullptr;
    const char* password_ = nullptr;
    uint32_t lastAttempt_ = 0;
    bool online_ = false;
};
