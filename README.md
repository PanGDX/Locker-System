# Makers' Locker System

Purpose: software to operate the Hub's locker system as well as email automation 


Main code:
- run ...


File descriptions
- gui.py
    - The main file. Operates the graphical interface of the entire system. Allows admins to lock and unlock lockers
- bluetooth_service.py
    - establish a BLE connection with the ESP32 for sending and receiving json data
- email_service.py
    - used to automate sending emails through Microsoft Outlook
- locker_logic.py
    - A utility file used to manage the locker states and the local json file


- main.ino
    - The code for the ESP32. ESP32 has two cores. Core 1 will be for updating, locking and unlocking the mechanical lockers. The second core will be for establishing a BLE connection and receiving data.

# Libs
ArduinoJson by Benoit Blanchon v.7.4.2
Async TCP by ESP32Async v3.4.9
ESP Async Webserver by ESP32Async v3.8.1