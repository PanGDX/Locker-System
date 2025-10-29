// FileManager.cpp

#include <LittleFS.h>
#include "FileManager.h"
#include "config.h"

// Define the global JSON document
StaticJsonDocument<2048> data_json;

bool fileManagerSetup() {
  if (!LittleFS.begin(true)) {
    Serial.println("An Error has occurred while mounting LittleFS");
    return false;
  }
  Serial.println("LittleFS mounted successfully.");

  if (!LittleFS.exists(DETAILS_FILE_PATH)) {
    Serial.println("details.json not found, creating default.");
    File file = LittleFS.open(DETAILS_FILE_PATH, "w");
    if (!file) {
      Serial.println("Failed to create default file.");
      return false;
    }
    // Initialize with a root object containing a "lockers" object
    file.print("{\"lockers\":{}}");
    file.close();
  }

  File file = LittleFS.open(DETAILS_FILE_PATH, "r");
  DeserializationError error = deserializeJson(data_json, file);
  file.close();
  
  if (error) {
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.c_str());
    return false;
  }

  Serial.println("Current locker data loaded from LittleFS:");
  serializeJsonPretty(data_json, Serial);
  Serial.println();
  return true;
}

void saveDataToJsonFile() {
  File file = LittleFS.open(DETAILS_FILE_PATH, "w");
  if (!file) {
    Serial.println("Failed to open details.json for writing.");
    return;
  }
  if (serializeJson(data_json, file) == 0) {
    Serial.println("Failed to write to file");
  }
  file.close();
  Serial.println("Data saved to LittleFS.");
  serializeJsonPretty(data_json, Serial);
  Serial.println();
}


/**
 * @brief Creates or updates the data for a specific locker.
 * 
 * This function now takes a jobid and creates a nested object
 * with both a "password" and a "jobid" key, matching the new style.
 * 
 * New JSON structure for a locker:
 * "locker_A": {
 *   "password": "...",
 *   "jobid": "..."
 * }
 */
void editLockerData(const char* lockerId, const char* password, const char* jobid) {
  // Ensure the top-level 'lockers' object exists
  if (!data_json.containsKey("lockers")) {
    data_json.createNestedObject("lockers");
  }
  JsonObject lockers = data_json["lockers"];
  
  // Create or get the specific locker's data object
  JsonObject lockerData = lockers.createNestedObject(lockerId);
  
  // ** CHANGE **: Populate the nested object with the new keys
  lockerData["password"] = password; // Using "password" instead of "passcode"
  lockerData["jobid"] = jobid;

  saveDataToJsonFile();
}


void removeLockerData(const char* lockerId) {
  if (data_json.containsKey("lockers")) {
    data_json["lockers"].remove(lockerId);
    saveDataToJsonFile();
  }
}