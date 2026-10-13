#pragma once

// Test double for GPIO and echo timing, used only by the desktop test executable.
constexpr int OUTPUT = 1;
constexpr int INPUT = 0;
constexpr int HIGH = 1;
constexpr int LOW = 0;
void pinMode(int pin, int mode);
void digitalWrite(int pin, int value);
void delayMicroseconds(unsigned int microseconds);
unsigned long pulseIn(int pin, int state, unsigned long timeout);
