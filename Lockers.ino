#include <WiFi.h>
#include <ArduinoJson.h>
#include "LittleFS.h"
#include <ESPAsyncWebServer.h>
#include <AsyncTCP.h>
#include <WifiPassword.h> // Assumes you have this header file with SSID and PASSWORD defined
#include <LiquidCrystal_I2C.h>
#include <Keypad.h>

// Numpad Setup
const int ROW_NUM = 4;
const int COLUMN_NUM = 3;

char keys[ROW_NUM][COLUMN_NUM] = {
  {'1', '2', '3'},
  {'4', '5', '6'},
  {'7', '8', '9'},
  {'*', '0', '#'}
};

byte pin_rows[ROW_NUM] = {33, 25, 26, 27};
byte pin_column[COLUMN_NUM] = {23, 19, 18};

Keypad keypad = Keypad(makeKeymap(keys), pin_rows, pin_column, ROW_NUM, COLUMN_NUM);

// LCD
int lcdColumns = 16;
int lcdRows = 2;
LiquidCrystal_I2C lcd(0x3F, lcdColumns, lcdRows);

// --- Network Configuration ---
const char *ssid = SSID;
const char *password = PASSWORD;

AsyncWebServer server(80);

IPAddress local_IP(192, 168, 68, 184);
IPAddress gateway(192, 168, 68, 1);
IPAddress subnet(255, 255, 252, 0);

// --- File System Configuration ---
const char* detailsFilePath = "/details.json";

// --- Global variables for display and input ---
String input_password = "";
String current_display_line1 = "Put Your Password:";
String current_display_line2 = "";
unsigned long display_timer_start = 0;
int display_timeout = 0;

// --- JSON Data Store ---
StaticJsonDocument<2048> data_json;

// --- Function Prototypes ---
void update_display();
void check_password_and_unlock();
void edit_data_and_save(const char* lockerId, JsonObject lockerData);
void remove_data_and_save(const char* lockerId);


// --- WiFi Connection Logic ---
void WiFiConnect() {
  WiFi.mode(WIFI_STA);
  Serial.print("Connecting to ");
  Serial.println(ssid);
  if (!WiFi.config(local_IP, gateway, subnet)) {
    Serial.println("STA Failed to configure");
  }
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

// --- WiFi Event Handlers ---
void WiFiStationConnected(WiFiEvent_t event, WiFiEventInfo_t info) { Serial.println("Connected to AP successfully!"); }
void WiFiGotIP(WiFiEvent_t event, WiFiEventInfo_t info) { Serial.println("WiFi connected"); Serial.print("IP address: "); Serial.println(WiFi.localIP()); }
void WiFiStationDisconnected(WiFiEvent_t event, WiFiEventInfo_t info) { Serial.println("Disconnected. Reason: " + String(info.wifi_sta_disconnected.reason)); Serial.println("Trying to Reconnect"); WiFi.begin(ssid, password); }

// --- File System Setup ---
bool LittleFSSetup() {
  if (!LittleFS.begin(true)) {
    Serial.println("An Error has occurred while mounting LittleFS");
    return false;
  }
  Serial.println("LittleFS mounted successfully.");

  if (!LittleFS.exists(detailsFilePath)) {
    Serial.println("details.json not found, creating default.");
    File file = LittleFS.open(detailsFilePath, "w");
    if (!file) {
      Serial.println("Failed to create default file.");
      return false;
    }
    file.print("{\"lockers\": {}}");
    file.close();
  }

  File file = LittleFS.open(detailsFilePath, "r");
  String fileContent = file.readString();
  DeserializationError error = deserializeJson(data_json, fileContent);
  if (error) {
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.c_str());
    return false;
  }
  Serial.println("Current content of details.json:");
  serializeJsonPretty(data_json, Serial);
  Serial.println();
  file.close();
  return true;
}

void keypadEvent(KeypadEvent key) {
  switch (keypad.getState()) {
    case PRESSED:
      Serial.print("Pressed: ");
      Serial.println(key);

      if (key >= '0' && key <= '9') {
        input_password += key;
        current_display_line2 = input_password;
      } else if (key == '*') { // Submit
        check_password_and_unlock();
      } else if (key == '#') { // Clear
        input_password = "";
        current_display_line2 = "";
      }
      update_display();
      break;

    case RELEASED:
    case HOLD:
      break;
  }
}

void setup() {
  Serial.begin(115200);

  if (!LittleFSSetup()) {
    Serial.println("CRITICAL: LittleFS failed to initialize. Halting.");
    while (1) { delay(1000); }
  }

  lcd.init();
  lcd.backlight();
  update_display();

  WiFiConnect();
  WiFi.onEvent(WiFiStationConnected, ARDUINO_EVENT_WIFI_STA_CONNECTED);
  WiFi.onEvent(WiFiGotIP, ARDUINO_EVENT_WIFI_STA_GOT_IP);
  WiFi.onEvent(WiFiStationDisconnected, ARDUINO_EVENT_WIFI_STA_DISCONNECTED);

  server.on("/details", HTTP_GET, [](AsyncWebServerRequest *request) {
    Serial.println("GET request for /details");
    request->send(LittleFS, detailsFilePath, "application/json");
  });

  server.on("/actions", HTTP_POST,
    [](AsyncWebServerRequest *request) {}, NULL,
    [](AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t index, size_t total) {
      if (index + len != total) return;

      Serial.println("POST request to /actions");
      StaticJsonDocument<512> received_doc;
      DeserializationError error = deserializeJson(received_doc, (const char*)data, len);

      if (error) {
        Serial.printf("deserializeJson() failed: %s\n", error.c_str());
        request->send(400, "application/json", "{\"status\":\"error\", \"message\":\"Invalid JSON\"}");
        return;
      }

      if (!received_doc.containsKey("signal") || !received_doc.containsKey("locker")) {
        request->send(400, "application/json", "{\"status\":\"error\", \"message\":\"'signal' or 'locker' key missing\"}");
        return;
      }

      const char* signal = received_doc["signal"];
      const char* lockerId = received_doc["locker"];

      if (strcmp(signal, "unlock") == 0) {
        Serial.printf("Received UNLOCK signal for locker %s\n", lockerId);
        unlock(lockerId);
        remove_data_and_save(lockerId);
        request->send(200, "application/json", "{\"status\":\"approved\"}");
      } else if (strcmp(signal, "lock") == 0) {
        if (!received_doc.containsKey("data")) {
          request->send(400, "application/json", "{\"status\":\"error\", \"message\":\"'data' key missing for lock signal\"}");
          return;
        }
        JsonObject lockerData = received_doc["data"].as<JsonObject>();
        edit_data_and_save(lockerId, lockerData);
        request->send(200, "application/json", "{\"status\":\"approved\"}");
      } else {
        request->send(400, "application/json", "{\"status\":\"error\", \"message\":\"Unknown signal\"}");
      }
    }
  );

  server.onNotFound([](AsyncWebServerRequest *request) {
    request->send(404, "application/json", "{\"error\":\"Not Found\"}");
  });

  server.begin();
  Serial.println("HTTP server started.");

  keypad.addEventListener(keypadEvent);
}

void loop() {
  keypad.getKey();

  if (display_timeout > 0 && millis() - display_timer_start > display_timeout) {
    current_display_line1 = "Put Your Password:";
    current_display_line2 = "";
    input_password = "";
    display_timeout = 0;
    update_display();
  }
}

void update_display() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(current_display_line1);
  lcd.setCursor(0, 1);
  lcd.print(current_display_line2);
}

void check_password_and_unlock() {
  JsonObject lockers = data_json["lockers"];
  bool password_found = false;

  for (JsonPair locker : lockers) {
    const char* current_locker_id = locker.key().c_str();
    const char* correct_passcode = locker.value()["passcode"];

    if (input_password == correct_passcode) {
      unlock(current_locker_id);
      current_display_line1 = "Locker Unlocked:";
      current_display_line2 = current_locker_id;
      display_timer_start = millis();
      display_timeout = 10000; // 10 seconds
      password_found = true;
      break; 
    }
  }

  if (!password_found) {
    current_display_line1 = "NO VALID LOCKERS";
    current_display_line2 = "";
    display_timer_start = millis();
    display_timeout = 5000; // 5 seconds
  }

  input_password = "";
  update_display();
}

void edit_data_and_save(const char* lockerId, JsonObject lockerData) {
  data_json["lockers"][lockerId] = lockerData;
  File file = LittleFS.open(detailsFilePath, "w");
  if (!file) {
    Serial.println("Failed to open details.json for writing.");
    return;
  }
  serializeJson(data_json, file);
  file.close();
  Serial.printf("Data for locker %s updated and saved.\n", lockerId);
  serializeJsonPretty(data_json, Serial);
  Serial.println();
}

void remove_data_and_save(const char* lockerId) {
  data_json["lockers"].remove(lockerId);
  File file = LittleFS.open(detailsFilePath, "w");
  if (!file) {
    Serial.println("Failed to open details.json for writing.");
    return;
  }
  serializeJson(data_json, file);
  file.close();
  Serial.printf("Data for locker %s removed and saved.\n", lockerId);
  serializeJsonPretty(data_json, Serial);
  Serial.println();
}

void unlock(String locker_id) {
  Serial.print("Unlocking: ");
  Serial.println(locker_id);
  // --- TODO: Add your actual motor/solenoid unlock code here for the specified locker_id ---
}

void lock(String locker_id) {
  Serial.print("Locking: ");
  Serial.println(locker_id);
  // --- TODO: Add your actual motor/solenoid lock code here for the specified locker_id ---
}