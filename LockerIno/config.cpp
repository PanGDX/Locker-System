// config.cpp -- NEW FILE

#include "config.h" // Include the header to ensure definitions match declarations

// --- DEFINITIONS ---
// This is the one and only place where memory for these variables is allocated.

const IPAddress LOCAL_IP(192, 168, 68, 184);
const IPAddress GATEWAY(192, 168, 68, 1);
const IPAddress SUBNET(255, 255, 252, 0);

const char* DETAILS_FILE_PATH = "/details.json";

const int UNLOCK_DISPLAY_TIMEOUT_MS = 10000;
const int ERROR_DISPLAY_TIMEOUT_MS = 5000;