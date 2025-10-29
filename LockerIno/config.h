// config.h -- CORRECTED

#ifndef CONFIG_H
#define CONFIG_H

#include <IPAddress.h>

// --- DECLARATIONS ---
// The 'extern' keyword promises that these variables are DEFINED in a .cpp file somewhere.

extern const IPAddress LOCAL_IP;
extern const IPAddress GATEWAY;
extern const IPAddress SUBNET;

extern const char* DETAILS_FILE_PATH;

extern const int UNLOCK_DISPLAY_TIMEOUT_MS;
extern const int ERROR_DISPLAY_TIMEOUT_MS;

#endif // CONFIG_H