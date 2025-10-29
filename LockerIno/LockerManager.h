// LockerManager.h

#ifndef LOCKER_MANAGER_H
#define LOCKER_MANAGER_H

#include <Arduino.h>

// 1. Define a structure to hold the mapping for each locker
struct Locker {
  const char* id;
  int motorPin;
};

// 2. Create an array of Locker structs to define all your lockers.
//    This is where you map each string ID to a specific pin number.
const Locker lockers[] = {
  {"locker_A", 2},
  {"locker_B", 3},
  {"locker_C", 4},
  {"locker_D", 5}
  // Add more lockers here as needed
};

const int numLockers = sizeof(lockers) / sizeof(lockers[0]);

// 3. Helper function to find the pin number for a given locker ID.
//    It loops through the array and returns the pin if the ID is found.
int getPinForLocker(String locker_id) {
  for (int i = 0; i < numLockers; i++) {
    if (locker_id.equals(lockers[i].id)) {
      return lockers[i].motorPin;
    }
  }
  return -1; // Return -1 or another invalid pin number if the ID is not found
}

#endif // LOCKER_MANAGER_H