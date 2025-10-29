import requests
import json
import os
import shutil

DATA_FILE = './data/details.json'
DATA_FILE_TMP = './data/details.json.tmp'
ESP32_IP = "192.168.68.184"

class ESP32detailsManager:
    """
    Manages synchronization of a JSON details file with an ESP32 server.
    """
    def __init__(self, esp32_ip):
        self.esp32_ip = esp32_ip
        self.local_file = DATA_FILE
        self.local_file_tmp = DATA_FILE_TMP
        self.url = f"http://{self.esp32_ip}"
        self.get_url = f"{self.url}/details"
        self.post_url = f"{self.url}/actions"
        self.headers = {'Content-Type': 'application/json'}
        print(f"--- details Manager Initialized for ESP32 at {self.esp32_ip} ---")

    def sync_from_esp32(self):
        """Downloads the details from the ESP32 and replaces the local version."""
        print(f"-> Attempting to GET details from {self.get_url}...")
        try:
            response = requests.get(self.get_url, timeout=5)
            response.raise_for_status()

            self.make_backup()

            with open(self.local_file, 'w') as f:
                json.dump(response.json(), f, indent=4)
            print(f"   Success! Synced and saved details to '{self.local_file}'")

            self.delete_backup()
            return True
        except requests.exceptions.RequestException as e:
            print(f"   Error: Could not get details from ESP32. {e}")
            return False

    def make_backup(self):
        print("-> Making backup")
        # Ensure the data directory exists before trying to copy
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        if os.path.exists(DATA_FILE):
            shutil.copy2(DATA_FILE, DATA_FILE_TMP)
        return True
    
    def delete_backup(self):
        print("-> Deleting backup")
        if(os.path.exists(DATA_FILE_TMP)):
            os.remove(DATA_FILE_TMP)
        return True


    def send_unlock_signal(self, locker_id: str):
        """
        Sends an unlock json signal {"signal": "unlock"} to the esp32.
        Waits for json response. If it is "error", raises an error. 
        If it is approved, returns True.
        """
        payload = {"signal": "unlock", "locker": str(locker_id)}
        print(f"-> Sending UNLOCK signal to {self.post_url}...")
        try:
            # Use the json parameter to automatically serialize the dict and set headers
            response = requests.post(self.post_url, json=payload, timeout=5)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            
            response_json = response.json()
            print(f"   Server response: {response_json}")

            # Check for application-level error in the response
            if response_json["status"] == "approved":
                print("   Unlock signal approved.")
                return True
            else:
                # Raise an error if status is not 'approved'
                raise Exception(f"Unlock failed. ESP32 response: {response_json}")

        except requests.exceptions.RequestException as e:
            print(f"   Error: Could not send unlock signal to ESP32. {e}")
            raise  # Re-raise the exception after logging
        except json.JSONDecodeError:
            print(f"   Error: Could not decode JSON response from ESP32. Response text: {response.text}")
            raise
        except Exception as e:
            print(f"   An unexpected error occurred: {e}")
            raise


    def send_occupy_signal(self, locker_id: str, jobid: str, password: str = ""):
        """
        Sends a lock json signal {"signal": "lock", "password" : ""} to the esp32.
        Blank "" is no password. Waits for json response. If it is "error", raises an error.
        If it is approved, returns True.
        """
        payload = {"signal": "occupy", "locker": str(locker_id), "password": str(password), "jobid": str(jobid)}
        print(f"-> Sending LOCK signal: {payload}...")
        try:
            response = requests.post(self.post_url, json=payload, timeout=5)
            response.raise_for_status()
            
            response_json = response.json()
            print(f"   Server response: {response_json}")

            if response_json["status"] == "approved":
                print("   Lock signal approved.")
                return True
            else:
                raise Exception(f"Lock failed. ESP32 response: {response_json}")

        except requests.exceptions.RequestException as e:
            print(f"   Error: Could not send lock signal to ESP32. {e}")
            raise
        except json.JSONDecodeError:
            print(f"   Error: Could not decode JSON response from ESP32. Response text: {response.text}")
            raise
        except Exception as e:
            print(f"   An unexpected error occurred: {e}")
            raise



if __name__ == '__main__':
    esp32_manager = ESP32detailsManager(ESP32_IP)
    print("Most common error: You are not connected to EDIC_LAN wifi")
    
    esp32_manager.sync_from_esp32()
    esp32_manager.send_lock_signal(
        locker_id= "101",
        password= "1231"
    )
    esp32_manager.send_unlock_signal(
        locker_id= "101"
    )