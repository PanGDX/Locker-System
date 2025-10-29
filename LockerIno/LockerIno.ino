// MyLockerProject.ino

#include "config.h"
#include "FileManager.h"
#include "HardwareManager.h"
#include "NetworkManager.h"

void setup() {
  Serial.begin(115200);
  Serial.println("\n\n--- Smart Locker System Booting Up ---");

  // Initialize file system first to load data
  if (!fileManagerSetup()) {
    Serial.println("CRITICAL: LittleFS failed. Halting.");
    while (true) { delay(1000); }
  }

  // Initialize hardware components (LCD, Keypad)
  hardwareSetup();

  // Initialize WiFi and Web Server
  networkSetup();

  Serial.println("--- System Ready ---");
}

void loop() {
  // Check for keypad input
  handleKeypadInput();

  // Handle display timeouts (e.g., clearing "Unlocked" message)
  handleLcdTimeout();
}