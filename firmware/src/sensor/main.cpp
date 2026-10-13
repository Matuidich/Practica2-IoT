#include <Arduino.h>
#include "Config.h"
#include "UltrasonicSensor.h"
#include "WifiConnection.h"
#include "TcpConnection.h"

namespace {
UltrasonicSensor sensor(Config::TRIG_PIN, Config::ECHO_PIN);
WifiConnection wifi;
TcpConnection tcp;
uint32_t sampledAt = 0;
uint32_t sequence = 0;
}

void setup() {
    Serial.begin(Config::SERIAL_BAUD);
    sensor.begin();
    wifi.begin(IOT_WIFI_SSID, IOT_WIFI_PASSWORD);
    tcp.begin(IOT_SERVER_HOST, IOT_SERVER_PORT, Protocol::Role::Sensor, Config::TCP_SETTINGS);
    sampledAt = millis() - Config::SAMPLE_MS;
}

void loop() {
    uint32_t now = millis();
    tcp.update(now, wifi.update(now));
    Protocol::Message response;
    while (tcp.nextMessage(response)) { /* Consume optional server diagnostics. */ }
    now = millis();
    if (now - sampledAt < Config::SAMPLE_MS) { yield(); return; }
    sampledAt = now;
    UltrasonicSensor::Measurement measurement = sensor.getDistance();
    float distance = 0;
    bool valid = measurement.distanceCm(distance);
    char line[100];
    ++sequence;
    if (Protocol::ProtocolCodec::measurement(distance, valid, sequence, line, sizeof(line))) {
        bool sent = tcp.ready() && tcp.sendLine(line);
        Serial.printf("sample seq=%lu t_ms=%lu distance_cm=%.2f valid=%d sent=%d\n",
                      static_cast<unsigned long>(sequence), static_cast<unsigned long>(now),
                      static_cast<double>(distance), valid, sent);
    }
    yield();
}
