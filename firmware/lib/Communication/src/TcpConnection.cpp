#include "TcpConnection.h"
#include <errno.h>
#include <lwip/sockets.h>
#include <string.h>

void TcpConnection::begin(const char* host, uint16_t port, Protocol::Role role, ConnectionSettings settings) {
    host_ = host;
    port_ = port;
    role_ = role;
    settings_ = settings;
    lastAttempt_ = millis() - settings_.retryMs;
}

void TcpConnection::disconnect() {
    client_.stop();
    state_ = State::Disconnected;
    input_.reset();
    outputSize_ = outputSent_ = 0;
    lastAttempt_ = millis();
}

void TcpConnection::update(uint32_t now, bool wifiOnline) {
    if (!wifiOnline) {
        if (state_ != State::Disconnected) { disconnect(); }
        return;
    }
    if (state_ != State::Disconnected && !client_.connected()) { disconnect(); }
    now = millis();
    if (state_ == State::Disconnected) {
        if (now - lastAttempt_ < settings_.retryMs) { return; }
        lastAttempt_ = now;
        IPAddress address;
        // Use a LAN IPv4 address; avoid a blocking DNS lookup in the control loop.
        if (!address.fromString(host_) || !client_.connect(address, port_, settings_.connectTimeoutMs)) { return; }
        client_.setNoDelay(true);
        state_ = State::Registering;
        registeredAt_ = millis();
        char line[80];
        if (!Protocol::ProtocolCodec::registration(role_, line, sizeof(line)) || !sendLine(line)) { disconnect(); }
    }
    flushTransmit(millis());
    if (state_ == State::Registering && millis() - registeredAt_ >= settings_.registerTimeoutMs) { disconnect(); }
}

bool TcpConnection::sendLine(const char* line) {
    if (state_ == State::Disconnected || outputSize_ != 0) { return false; }
    size_t length = strlen(line);
    if (!length || length >= sizeof(output_)) { return false; }
    memcpy(output_, line, length);
    outputSize_ = length;
    outputSent_ = 0;
    txStartedAt_ = millis();
    flushTransmit(txStartedAt_);
    return state_ != State::Disconnected;
}

void TcpConnection::flushTransmit(uint32_t now) {
    if (!outputSize_) { return; }
    // A bounded pending message and nonblocking writes keep LED timing responsive.
    int written = ::send(client_.fd(), output_ + outputSent_, outputSize_ - outputSent_, MSG_DONTWAIT);
    if (written > 0) {
        outputSent_ += static_cast<size_t>(written);
        if (outputSent_ == outputSize_) { outputSize_ = outputSent_ = 0; }
    } else if (written == 0 || (errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR)) {
        disconnect();
    }
    if (outputSize_ && now - txStartedAt_ >= static_cast<uint32_t>(settings_.connectTimeoutMs)) { disconnect(); }
}

bool TcpConnection::nextMessage(Protocol::Message& message) {
    if (state_ == State::Disconnected) { return false; }
    size_t budget = Protocol::MAX_LINE_BYTES + 2;
    while (budget-- && client_.available()) {
        int byte = client_.read();
        if (byte < 0) { break; }
        Protocol::LineBuffer::Result result = input_.push(static_cast<char>(byte));
        if (result == Protocol::LineBuffer::Result::Error) { disconnect(); return false; }
        if (result != Protocol::LineBuffer::Result::Ready) { continue; }
        if (!Protocol::ProtocolCodec::parse(input_.line(), message)) {
            Serial.println("Invalid server message; disconnecting");
            disconnect();
            return false;
        }
        if (message.kind == Protocol::Kind::Error) {
            Serial.print("Server error: ");
            Serial.println(message.errorCode);
            disconnect();
            return false;
        }
        if (state_ == State::Registering) {
            if (message.kind != Protocol::Kind::Ok || message.role != role_) { disconnect(); return false; }
            state_ = State::Ready;
            Serial.println("TCP registered");
            continue;
        }
        return true;
    }
    return false;
}
