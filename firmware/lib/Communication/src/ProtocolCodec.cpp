#include "ProtocolCodec.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

namespace {
struct Argument { const char* key; const char* value; };

bool isLetter(char c) { return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z'); }
bool isDigit(char c) { return c >= '0' && c <= '9'; }

char* nextToken(char*& cursor) {
    while (*cursor == ' ') { ++cursor; }
    if (*cursor == '\0') { return nullptr; }
    char* start = cursor;
    while (*cursor && *cursor != ' ') { ++cursor; }
    if (*cursor) { *cursor++ = '\0'; }
    return start;
}

const char* argument(const Argument* args, size_t count, const char* key) {
    for (size_t i = 0; i < count; ++i) {
        if (strcmp(args[i].key, key) == 0) { return args[i].value; }
    }
    return nullptr;
}

bool unsignedInteger(const char* value, uint32_t& result) {
    if (!value || !*value) { return false; }
    uint32_t parsed = 0;
    for (const char* c = value; *c; ++c) {
        if (!isDigit(*c)) { return false; }
        uint32_t digit = static_cast<uint32_t>(*c - '0');
        if (parsed > (UINT32_MAX - digit) / 10U) { return false; }
        parsed = parsed * 10U + digit;
    }
    result = parsed;
    return true;
}

bool distanceValue(const char* value, double& distance) {
    if (!value || !*value) { return false; }
    bool dot = false;
    size_t digits = 0;
    for (const char* c = value; *c; ++c) {
        if (*c == '.' && !dot) { dot = true; }
        else if (isDigit(*c)) { ++digits; }
        else { return false; }
    }
    if (!digits || value[strlen(value) - 1] == '.') { return false; }
    distance = strtod(value, nullptr);
    return isfinite(distance) && distance > 0;
}

bool ledMode(const char* value, Protocol::LedMode& mode) {
    if (!value) { return false; }
    if (strcmp(value, "off") == 0) { mode = Protocol::LedMode::Off; }
    else if (strcmp(value, "on") == 0) { mode = Protocol::LedMode::On; }
    else if (strcmp(value, "blink_2") == 0) { mode = Protocol::LedMode::Blink2; }
    else if (strcmp(value, "blink_4") == 0) { mode = Protocol::LedMode::Blink4; }
    else { return false; }
    return true;
}

const char* knownError(const char* value) {
    static const char* const codes[] = {
        "BAD_MESSAGE", "LINE_TOO_LONG", "REGISTER_REQUIRED", "REGISTER_TIMEOUT",
        "ROLE_IN_USE", "WRONG_ROLE", "ALREADY_REGISTERED", "UNSUPPORTED_VERSION"
    };
    for (const char* code : codes) {
        if (value && strcmp(value, code) == 0) { return code; }
    }
    return nullptr;
}

bool fits(int length, size_t capacity) { return length > 0 && static_cast<size_t>(length) < capacity; }
}

namespace Protocol {
bool ProtocolCodec::parse(const char* line, Message& message) {
    message = Message{};
    if (!line || !*line || strlen(line) > MAX_LINE_BYTES) { return false; }
    char copy[MAX_LINE_BYTES + 1];
    strcpy(copy, line);
    for (char* c = copy; *c; ++c) {
        if (*c < 32 || *c > 126) { return false; }
        if (*c == ',') { *c = ' '; }
    }
    char* cursor = copy;
    char* command = nextToken(cursor);
    if (!command) { return false; }
    Argument args[4];
    size_t count = 0;
    for (char* token = nextToken(cursor); token; token = nextToken(cursor)) {
        if (count == 4) { return false; }
        char* equals = strchr(token, '=');
        if (!equals || equals == token || !equals[1]) { return false; }
        *equals = '\0';
        if (!isLetter(token[0])) { return false; }
        for (char* c = token; *c; ++c) {
            if (!isLetter(*c) && !isDigit(*c)) { return false; }
        }
        for (char* c = equals + 1; *c; ++c) {
            if (!isLetter(*c) && !isDigit(*c) && *c != '_' && *c != '.' && *c != '+' && *c != '-') { return false; }
        }
        if (argument(args, count, token)) { return false; }
        args[count++] = {token, equals + 1};
    }
    const char* sequence = argument(args, count, "seq");
    message.hasSequence = sequence != nullptr;
    if (sequence && !unsignedInteger(sequence, message.sequence)) { return false; }
    size_t payloadCount = count - (message.hasSequence ? 1 : 0);

    if (strcmp(command, "REGISTER") == 0 || strcmp(command, "OK") == 0) {
        const char* type = argument(args, count, "type");
        const char* version = argument(args, count, "version");
        if (message.hasSequence || !type || count != (version ? 2U : 1U)) { return false; }
        if (strcmp(type, "sensor") == 0) { message.role = Role::Sensor; }
        else if (strcmp(type, "actuator") == 0) { message.role = Role::Actuator; }
        else { return false; }
        if (version && strcmp(version, "1") != 0) {
            message.errorCode = "UNSUPPORTED_VERSION";
            return false;
        }
        message.hasVersion = version != nullptr;
        message.kind = strcmp(command, "REGISTER") == 0 ? Kind::Register : Kind::Ok;
    } else if (strcmp(command, "POST") == 0) {
        if (payloadCount != 1) { return false; }
        const char* distance = argument(args, count, "distance");
        const char* status = argument(args, count, "status");
        if (distance) {
            if (!distanceValue(distance, message.distance)) { return false; }
            message.validDistance = true;
        } else if (!status || strcmp(status, "invalid") != 0) { return false; }
        message.kind = Kind::Post;
    } else if (strcmp(command, "SET") == 0) {
        if (payloadCount != 3 || !ledMode(argument(args, count, "redLed"), message.red)
            || !ledMode(argument(args, count, "yellowLed"), message.yellow)
            || !ledMode(argument(args, count, "greenLed"), message.green)) { return false; }
        message.kind = Kind::Set;
    } else if (strcmp(command, "APPLIED") == 0) {
        if (payloadCount) { return false; }
        message.kind = Kind::Applied;
    } else if (strcmp(command, "ERROR") == 0) {
        const char* code = knownError(argument(args, count, "code"));
        if (count != 1 || !code) { return false; }
        message.kind = Kind::Error;
        message.errorCode = code;
    } else { return false; }
    return true;
}

const char* ProtocolCodec::kindName(Kind kind) {
    switch (kind) {
        case Kind::Register: return "REGISTER";
        case Kind::Post: return "POST";
        case Kind::Set: return "SET";
        case Kind::Ok: return "OK";
        case Kind::Applied: return "APPLIED";
        case Kind::Error: return "ERROR";
        default: return "UNKNOWN";
    }
}

bool ProtocolCodec::registration(Role role, char* output, size_t capacity) {
    if (role == Role::Unknown) { return false; }
    return fits(snprintf(output, capacity, "REGISTER type=%s version=1\n", role == Role::Sensor ? "sensor" : "actuator"), capacity);
}

bool ProtocolCodec::measurement(double distance, bool valid, uint32_t sequence, char* output, size_t capacity) {
    if (valid && (!isfinite(distance) || distance <= 0)) { return false; }
    int length = valid ? snprintf(output, capacity, "POST seq=%lu distance=%.2f\n", static_cast<unsigned long>(sequence), distance)
                       : snprintf(output, capacity, "POST seq=%lu status=invalid\n", static_cast<unsigned long>(sequence));
    return fits(length, capacity);
}

bool ProtocolCodec::applied(const Message& command, char* output, size_t capacity) {
    int length = command.hasSequence ? snprintf(output, capacity, "APPLIED seq=%lu\n", static_cast<unsigned long>(command.sequence))
                                     : snprintf(output, capacity, "APPLIED\n");
    return fits(length, capacity);
}

LineBuffer::Result LineBuffer::push(char byte) {
    if (byte == '\n') {
        if (size_ && buffer_[size_ - 1] == '\r') { --size_; }
        if (size_ > MAX_LINE_BYTES) { reset(); return Result::Error; }
        buffer_[size_] = '\0';
        size_ = 0;
        return Result::Ready;
    }
    if (size_ >= MAX_LINE_BYTES + 1 || (size_ == MAX_LINE_BYTES && byte != '\r') || byte == '\0') {
        reset();
        return Result::Error;
    }
    buffer_[size_++] = byte;
    return Result::Pending;
}
}
