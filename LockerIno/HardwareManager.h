// HardwareManager.h

#ifndef HARDWARE_MANAGER_H
#define HARDWARE_MANAGER_H

#include <Arduino.h>

void hardwareSetup();
void handleKeypadInput();
void updateLcd(const String& line1, const String& line2);
void resetLcdWithTimeout(const String& line1, const String& line2, int timeout);
void handleLcdTimeout();

#endif // HARDWARE_MANAGER_H