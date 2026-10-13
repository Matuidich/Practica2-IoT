#pragma once
#include <WiFi.h>
#include "ProtocolCodec.h"

struct ConnectionSettings {
    uint32_t retryMs;
    uint32_t registerTimeoutMs;
    int32_t connectTimeoutMs;
};

class TcpConnection {
public:
    void begin(const char* host, uint16_t port, Protocol::Role role, ConnectionSettings settings = {2000, 3000, 300});
    void update(uint32_t now, bool wifiOnline);
    bool nextMessage(Protocol::Message& message);
    bool sendLine(const char* line);
    bool ready() const { return state_ == State::Ready; }
    void disconnect();
private:
    enum class State { Disconnected, Registering, Ready };
    void flushTransmit(uint32_t now);
    WiFiClient client_;
    Protocol::LineBuffer input_;
    State state_ = State::Disconnected;
    Protocol::Role role_ = Protocol::Role::Unknown;
    ConnectionSettings settings_ = {2000, 3000, 300};
    const char* host_ = nullptr;
    uint16_t port_ = 0;
    uint32_t lastAttempt_ = 0;
    uint32_t registeredAt_ = 0;
    uint32_t txStartedAt_ = 0;
    char output_[Protocol::MAX_LINE_BYTES + 2] = {};
    size_t outputSize_ = 0;
    size_t outputSent_ = 0;
};
