// NetworkManager.cpp

#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include "NetworkManager.h"
#include "config.h"
#include "LittleFS.h"
#include "WifiPassword.h" // Assumes you have this header file
#include "FileManager.h"  // For accessing files and JSON data

// Forward-declare from HardwareManager.cpp. In a larger project, you might
// create a "LockerControl.h" for these.
void unlock(String locker_id);
void lock(String locker_id);

// --- Server and Network Objects ---
AsyncWebServer server(80);

void onStationConnected(WiFiEvent_t event, WiFiEventInfo_t info) {
  Serial.println("Connected to AP successfully!");
}

void onGotIP(WiFiEvent_t event, WiFiEventInfo_t info) {
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void onStationDisconnected(WiFiEvent_t event, WiFiEventInfo_t info) {
  Serial.println("Disconnected. Reason: " + String(info.wifi_sta_disconnected.reason));
  Serial.println("Trying to Reconnect");
  WiFi.begin(SSID, PASSWORD);
}

void setupServerRouting() {
  server.on("/details", HTTP_GET, [](AsyncWebServerRequest *request) {
    Serial.println("GET request for /details");
    request->send(LittleFS, DETAILS_FILE_PATH, "application/json");
  });

  server.on("/actions", HTTP_POST,
    [](AsyncWebServerRequest *request) {}, NULL,
    [](AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t index, size_t total) {
      if (index + len != total) return; // Wait until all data is received

      Serial.println("POST request to /actions");
      StaticJsonDocument<512> received_doc;
      if (deserializeJson(received_doc, (const char*)data, len)) {
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
        unlock(lockerId);
        removeLockerData(lockerId);
        request->send(200, "application/json", "{\"status\":\"approved\", \"action\":\"unlocked\"}");
      } else if (strcmp(signal, "occupy") == 0) {
        if (!received_doc.containsKey("password")) {
          request->send(400, "application/json", "{\"status\":\"error\", \"message\":\"'password' key missing\"}");
          return;
        }
        if (!received_doc.containsKey("jobid")) {
          request->send(400, "application/json", "{\"status\":\"error\", \"message\":\"'jobid' key missing\"}");
          return;
        }

        const char* password = received_doc["password"];
        const char* jobid = received_doc["jobid"];
        lock(lockerId);
        editLockerData(lockerId, password, jobid);
        request->send(200, "application/json", "{\"status\":\"approved\", \"action\":\"occupied\"}");
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
}

void networkSetup() {
  WiFi.mode(WIFI_STA);
  Serial.print("Connecting to ");
  Serial.println(SSID);
  
  if (!WiFi.config(LOCAL_IP, GATEWAY, SUBNET)) {
    Serial.println("STA Failed to configure");
  }

  WiFi.onEvent(onStationConnected, ARDUINO_EVENT_WIFI_STA_CONNECTED);
  WiFi.onEvent(onGotIP, ARDUINO_EVENT_WIFI_STA_GOT_IP);
  WiFi.onEvent(onStationDisconnected, ARDUINO_EVENT_WIFI_STA_DISCONNECTED);

  WiFi.begin(SSID, PASSWORD);
  
  setupServerRouting();
}