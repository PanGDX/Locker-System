#include <WiFi.h>
#include <ArduinoJson.h>
#include "LittleFS.h"
#include <ESPAsyncWebServer.h>
#include <AsyncTCP.h>
#include <WifiPassword.h>
// --- Network Configuration ---
const char *ssid = SSID;
const char *password = PASSWORD;

AsyncWebServer server(80);

IPAddress local_IP(192, 168, 68, 184); // Note: Corrected the first octet to a valid private range value
IPAddress gateway(192, 168, 68, 1);
IPAddress subnet(255, 255, 252, 0);

// --- File System Configuration ---
const char* detailsFilePath = "/details.json";
const char* tempDetailsFilePath = "/details.json.tmp";

// --- WiFi Connection Logic ---
void WiFiConnect(){
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

// --- WiFi Event Handlers (Unchanged) ---
void WiFiStationConnected(WiFiEvent_t event, WiFiEventInfo_t info){ Serial.println("Connected to AP successfully!"); }
void WiFiGotIP(WiFiEvent_t event, WiFiEventInfo_t info){ Serial.println("WiFi connected"); Serial.print("IP address: "); Serial.println(WiFi.localIP()); }
void WiFiStationDisconnected(WiFiEvent_t event, WiFiEventInfo_t info){ Serial.println("Disconnected. Reason: " + String(info.wifi_sta_disconnected.reason)); Serial.println("Trying to Reconnect"); WiFi.begin(ssid, password); }

// --- File System Setup (More Robust) ---
bool LittleFSSetup(){
  if(!LittleFS.begin(true)){ // true = format if mount failed
    Serial.println("An Error has occurred while mounting LittleFS");
    return false;
  }
  Serial.println("LittleFS mounted successfully.");

  // If the main file doesn't exist, create a default one.
  if(!LittleFS.exists(detailsFilePath)){
    Serial.println("details.json not found, creating default.");
    File file = LittleFS.open(detailsFilePath, "w");
    if(!file){
      Serial.println("Failed to create default file.");
      return false;
    }
    file.print("{\"default\": true}");
    file.close();
  }
  else{
    File file = LittleFS.open(detailsFilePath, "r");
    String fileContent = file.readString();
    StaticJsonDocument<2048> doc; 
    DeserializationError error = deserializeJson(doc, fileContent);
    serializeJsonPretty(doc, Serial); 
  }
  return true;
}





void setup() {
  Serial.begin(115200);

  // Halt if LittleFS fails. The device cannot function without it.
  if (!LittleFSSetup()) {
    Serial.println("CRITICAL: LittleFS failed to initialize. Halting.");
    while(1) { delay(1000); }
  }

  WiFiConnect();

  WiFi.onEvent(WiFiStationConnected, ARDUINO_EVENT_WIFI_STA_CONNECTED);
  WiFi.onEvent(WiFiGotIP, ARDUINO_EVENT_WIFI_STA_GOT_IP);
  WiFi.onEvent(WiFiStationDisconnected, ARDUINO_EVENT_WIFI_STA_DISCONNECTED);

  // --- API Endpoint Definitions ---

  // GET: Retrieve the JSON file
  server.on("/details", HTTP_GET, [](AsyncWebServerRequest *request){
    Serial.println("GET request for /details");
    if (LittleFS.exists(detailsFilePath)) {
      request->send(LittleFS, detailsFilePath, "application/json");
    } else {
      request->send(404, "application/json", "{\"error\":\"File not found\"}");
    }
  });

  // POST: Update the JSON file safely
  server.on("/details", HTTP_POST, 
    [](AsyncWebServerRequest *request){},
    NULL,
    [](AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t index, size_t total){
      if (index == 0) {
        Serial.println("POST /details: Receiving file...");
        File file = LittleFS.open(tempDetailsFilePath, "w");
        if (!file) {
          Serial.println("Failed to open temp file for writing");
          request->send(500, "application/json", "{\"error\":\"Internal Server Error: Could not create temp file\"}");
          return;
        }
        file.close();
      }


      File file = LittleFS.open(tempDetailsFilePath, "a");
      if(file){
        file.write(data, len);
        file.close();
      }

      // When the last chunk has been received
      if (index + len == total) {
        Serial.println("POST /details: File received. Validating...");
        File tempFile = LittleFS.open(tempDetailsFilePath, "r");
        if (!tempFile) {
           request->send(500, "application/json", "{\"error\":\"Could not read temp file for validation\"}");
           return;
        }

        StaticJsonDocument<2048> doc;
        DeserializationError error = deserializeJson(doc, tempFile);
        tempFile.close();

        if (error) {
          // If JSON is invalid, delete the temp file and send an error
          LittleFS.remove(tempDetailsFilePath);
          Serial.print("JSON validation failed: ");
          Serial.println(error.c_str());
          request->send(400, "application/json", "{\"error\":\"Invalid JSON format\"}");
        } else {
          // If JSON is valid, replace the original file with the new one
          Serial.println("JSON is valid. Updating file.");
          LittleFS.remove(detailsFilePath);
          LittleFS.rename(tempDetailsFilePath, detailsFilePath);
          request->send(200, "application/json", "{\"success\":\"File updated successfully\"}");
        }
      }
    }
  );

  server.onNotFound([](AsyncWebServerRequest *request){
    request->send(404, "application/json", "{\"error\":\"Not Found\"}");
  });

  server.begin();
  Serial.println("HTTP server started.");
}

void loop() {
  // Empty. The async server handles everything.
}