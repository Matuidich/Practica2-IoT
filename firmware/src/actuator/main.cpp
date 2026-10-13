#include <Arduino.h>
#include "Config.h"
#include "LedController.h"
#include "WifiConnection.h"
#include "TcpConnection.h"

namespace {
LedController leds(Config::RED_PIN, Config::YELLOW_PIN, Config::GREEN_PIN);
WifiConnection wifi;
TcpConnection tcp;
uint32_t commandedAt = 0;
bool hasCommand = false;
}

void setup() {
    Serial.begin(Config::SERIAL_BAUD);
    leds.begin();
    wifi.begin(IOT_WIFI_SSID, IOT_WIFI_PASSWORD);
    tcp.begin(IOT_SERVER_HOST, IOT_SERVER_PORT, Protocol::Role::Actuator, Config::TCP_SETTINGS);
}

void loop() {
    uint32_t now = millis();
    // Handle stale outputs before attempting a new TCP connection.
    if (!tcp.ready() || (hasCommand && now - commandedAt >= Config::COMMAND_TIMEOUT_MS)) {
        leds.off(now);
        hasCommand = false;
    }
    leds.update(now);
    tcp.update(now, wifi.update(now));
    Protocol::Message command;
    while (tcp.nextMessage(command)) {
        now = millis();
        if (command.kind != Protocol::Kind::Set) {
            tcp.disconnect();
            break;
        }
        leds.apply(command, now);
        commandedAt = now;
        hasCommand = true;
        char response[80];
        if (Protocol::ProtocolCodec::applied(command, response, sizeof(response))) { tcp.sendLine(response); }
        Serial.printf("applied seq=%lu t_ms=%lu\n", static_cast<unsigned long>(command.sequence), static_cast<unsigned long>(now));
    }
    if (!tcp.ready()) { leds.off(millis()); hasCommand = false; }
    leds.update(millis());
    yield();
}
