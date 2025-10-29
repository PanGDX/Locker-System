// FileManager.h

#ifndef FILE_MANAGER_H
#define FILE_MANAGER_H

#include <ArduinoJson.h>

// This global JSON document will be accessible by other files
extern StaticJsonDocument<2048> data_json;

bool fileManagerSetup();
void saveDataToJsonFile();
void editLockerData(const char* lockerId, const char* password);
void removeLockerData(const char* lockerId);

#endif // FILE_MANAGER_H