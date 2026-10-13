#pragma once

#include <stddef.h>
#include <stdint.h>

namespace Protocol {
constexpr size_t MAX_LINE_BYTES = 256;
enum class Kind { Unknown, Register, Post, Set, Ok, Applied, Error };
enum class Role { Unknown, Sensor, Actuator };
enum class LedMode { Off, On, Blink2, Blink4 };

struct Message {
    Kind kind = Kind::Unknown;
    Role role = Role::Unknown;
    bool hasVersion = false;
    bool hasSequence = false;
    uint32_t sequence = 0;
    bool validDistance = false;
    double distance = 0;
    LedMode red = LedMode::Off;
    LedMode yellow = LedMode::Off;
    LedMode green = LedMode::Off;
    const char* errorCode = "BAD_MESSAGE";
};

class ProtocolCodec {
public:
    static bool parse(const char* line, Message& message);
    static const char* kindName(Kind kind);
    static bool registration(Role role, char* output, size_t capacity);
    static bool measurement(double distance, bool valid, uint32_t sequence, char* output, size_t capacity);
    static bool applied(const Message& command, char* output, size_t capacity);
};

class LineBuffer {
public:
    enum class Result { Pending, Ready, Error };
    Result push(char byte);
    const char* line() const { return buffer_; }
    void reset() { size_ = 0; buffer_[0] = '\0'; }
private:
    char buffer_[MAX_LINE_BYTES + 2] = {};
    size_t size_ = 0;
};
}
