// HardwareManager.cpp

#include <Keypad.h>
#include <LiquidCrystal_I2C.h>
#include "HardwareManager.h"
#include "config.h"
#include "FileManager.h" // Needed to access JSON data
#include "LockerManager.h" // Needed for unlocking


const int LCD_COLUMNS = 16;
const int LCD_ROWS = 2;
const int LCD_I2C_ADDRESS = 0x3F;

const int ROW_NUM = 4;
const int COLUMN_NUM = 3;

const byte PIN_ROWS[ROW_NUM] = {25,26,27,33};
const byte PIN_COLUMN[COLUMN_NUM] = {5, 18, 19};

const char KEYS[ROW_NUM][COLUMN_NUM] = {
  {'1', '2', '3'},
  {'4', '5', '6'},
  {'7', '8', '9'},
  {'*', '0', '#'}
};


// --- Function Prototypes for this file ---
void unlock(String locker_id);
void lock(String locker_id);
void checkPasswordAndUnlock();

// --- Hardware Objects ---
LiquidCrystal_I2C lcd(LCD_I2C_ADDRESS, LCD_COLUMNS, LCD_ROWS);
Keypad keypad = Keypad(makeKeymap(KEYS), (byte*)PIN_ROWS, (byte*)PIN_COLUMN, ROW_NUM, COLUMN_NUM);

// --- State Variables ---
String input_password = "";
String current_display_line1 = "Enter Password:";
String current_display_line2 = "";
unsigned long display_timer_start = 0;
int display_timeout = 0;

void keypadEvent(KeypadEvent key); // Forward declaration for addEventListener

void hardwareSetup() {
  lcd.init();
  lcd.backlight();
  updateLcd(current_display_line1, current_display_line2);
  keypad.addEventListener(keypadEvent);
}

void keypadEvent(KeypadEvent key) {
  if (keypad.getState() != PRESSED) return;

  Serial.print("Pressed: ");
  Serial.println(key);

  if (key >= '0' && key <= '9') {
    input_password += key;
    current_display_line2 = input_password;
  } else if (key == '*') { // Submit
    checkPasswordAndUnlock();
  } else if (key == '#') { // Clear
    input_password = "";
    current_display_line2 = "";
  }
  updateLcd(current_display_line1, current_display_line2);
}

void handleKeypadInput() {
  keypad.getKey();
}

void handleLcdTimeout() {
  if (display_timeout > 0 && millis() - display_timer_start > display_timeout) {
    current_display_line1 = "Enter Password:";
    current_display_line2 = "";
    input_password = "";
    display_timeout = 0;
    updateLcd(current_display_line1, current_display_line2);
  }
}

void updateLcd(const String& line1, const String& line2) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(line1);
  lcd.setCursor(0, 1);
  lcd.print(line2);
}

void resetLcdWithTimeout(const String& line1, const String& line2, int timeout) {
    current_display_line1 = line1;
    current_display_line2 = line2;
    display_timer_start = millis();
    display_timeout = timeout;
    input_password = "";
    updateLcd(current_display_line1, current_display_line2);
}

void checkPasswordAndUnlock() {
  JsonObject lockers = data_json["lockers"];
  bool password_found = false;

  for (JsonPair locker : lockers) {
    const char* current_locker_id = locker.key().c_str();
    const char* correct_passcode = locker.value()["passcode"];

    if (input_password == correct_passcode) {
      unlock(current_locker_id);
      removeLockerData(current_locker_id); // Occupied locker is now free
      resetLcdWithTimeout("Locker Unlocked:", current_locker_id, UNLOCK_DISPLAY_TIMEOUT_MS);
      password_found = true;
      break;
    }
  }

  if (!password_found) {
    resetLcdWithTimeout("INVALID PASSWORD", "", ERROR_DISPLAY_TIMEOUT_MS);
  }
}

// --- Actual Locker Control Logic ---
void unlock(String locker_id) {
  Serial.print("Unlocking: ");
  Serial.println(locker_id);
  
  int motorPin = getPinForLocker(locker_id);
  if (motorPin != -1) {
    pinMode(motorPin, OUTPUT);
    digitalWrite(motorPin, HIGH); // Assuming HIGH unlocks
    Serial.printf("  -> Motor on pin %d activated.\n", motorPin);
  } else {
    Serial.println("  -> ERROR: Pin for this locker ID not found!");
  }
}

void lock(String locker_id) {
  Serial.print("Locking: ");
  Serial.println(locker_id);
  
  int motorPin = getPinForLocker(locker_id);
  if (motorPin != -1) {
    pinMode(motorPin, OUTPUT);
    digitalWrite(motorPin, LOW); // Assuming LOW locks
    Serial.printf("  -> Motor on pin %d deactivated.\n", motorPin);
  } else {
    Serial.println("  -> ERROR: Pin for this locker ID not found!");
  }
}