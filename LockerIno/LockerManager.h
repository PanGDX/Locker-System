// LockerManager.h

#ifndef LOCKER_MANAGER_H
#define LOCKER_MANAGER_H

#include <Arduino.h>

struct Locker {
  const char* id;
  int motorPin;
};

const Locker lockers[] = {
  {"locker_A", 2},
  {"locker_B", 3},
  {"locker_C", 4},
};

const int numLockers = sizeof(lockers) / sizeof(lockers[0]);

int getPinForLocker(String locker_id) {
  for (int i = 0; i < numLockers; i++) {
    if (locker_id.equals(lockers[i].id)) {
      return lockers[i].motorPin;
    }
  }
  return -1; // Return -1 if the ID is not found
}

#endif // LOCKER_MANAGER_H