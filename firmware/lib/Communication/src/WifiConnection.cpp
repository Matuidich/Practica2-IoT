#include "WifiConnection.h"
#include <WiFi.h>

void WifiConnection::begin(const char* ssid, const char* password) {
    ssid_ = ssid;
    password_ = password;
    WiFi.mode(WIFI_STA);
    WiFi.setAutoReconnect(false);
    WiFi.begin(ssid_, password_);
    lastAttempt_ = millis();
}

bool WifiConnection::update(uint32_t now) {
    bool connected = WiFi.status() == WL_CONNECTED;
    if (connected && !online_) {
        Serial.print("WiFi IP: ");
        Serial.println(WiFi.localIP());
    }
    online_ = connected;
    if (!connected && now - lastAttempt_ >= 5000UL) {
        lastAttempt_ = now;
        WiFi.disconnect(false, false);
        WiFi.begin(ssid_, password_);
    }
    return connected;
}
