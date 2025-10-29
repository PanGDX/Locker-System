# Makers' Locker System


## Python Stack
Purpose: software to operate the Hub's locker system as well as email automation 


Main code:
- **gui.py**
    - The main file. Operates the graphical interface of the entire system. Allows admins to lock and unlock lockers


File descriptions
- **bluetooth_service.py**
    - establish a BLE connection with the ESP32 for sending and receiving json data
- **email_service.py**
    - used to automate sending emails through Microsoft Outlook
- **locker_logic.py**
    - A utility file used to manage the locker states and the local json file

### Testing


## ESP32 Stack
- main.ino
    - The code for the ESP32. ESP32 has two cores. Core 1 will be for updating, locking and unlocking the mechanical lockers. The second core will be for establishing a BLE connection and receiving data.
- WifiPassword.h
    - Define the SSID and password here


### Libraries for ESP32
- **ArduinoJson** by Benoit Blanchon v.7.4.2
- **Async TCP** by ESP32Async v3.4.9
- **ESP Async Webserver** by ESP32Async v3.8.1


### Testing
- Normal operation: upload, observe that the file is updated
- What happens if there is an error? How does an error occur

## How Things Work
- Install dependencies
- Upload program to ESP32 and ensure that both the computer and ESP32 are connected to the same network as defined in WifiPassword.h
- Run the GUI. Upon running the GUI, the ESP32 will send over its copy of details.json. This replaces the existing one. The GUI will make a temporary copy of the previous version which will be deleted after the session completes.
- Sending over the data: upon locking a locker, an email is sent to the respective individual + a modified copy of details.json is sent over to the ESP32. The ESP32 will make make a new file (no immediate replacement), replace the existing one if no error occurs, and then delete the copy. If any issue occurs, the previous copy is pulled back.



occupied false -> occupied true
will: lock, unlock and then lock again.

occupied true -> occupied false (take out)
will: unlock and then lock

what happens on startup? Some are occupied, some are not. All are locked. 



// GUI => unlock signal => unlock. Does not contain modify anything
// GUI => make occupy signal => 'lock' => puts a password or overrides existing password  


// one json file in esp32. Only contains: {"lockernum": {"password" : "", "jobid": ""}}
// one json files in local. Contains: {"lockernum": {"password" : "", "jobid": ""}} and 

edits to make
- Lockers.ino => change to new json file format
- gui.py + wifi_service change to new json file format
- map the buttons
- map the motors


EXAMPLE OF JSON. WILL FOLLOW THIS FORMAT.
{
    "302": {
        "occupied": true,
        "user": "asdasd",
        "email": "www@gmail.com",
        "job" : "123",
        "passcode": "214651"
    },
    "102": {
        "occupied": true,
        "user": "asdas",
        "email": "www@ww.com",
        "job": "234",
        "passcode": "819177"
    }
}




### How To Setup Entra
- Sign up for Entra ID using personal email through the student offer
- Verify student status
- New app: Mobile and desktop applications
- Take note of the client(application) ID and the tenant ID
- Ensure: Allow public client flows
