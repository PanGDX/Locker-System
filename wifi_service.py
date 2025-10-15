import requests
import json
import os
import time

class ESP32detailsManager:
    """
    Manages synchronization of a JSON details file with an ESP32 server.
    """
    def __init__(self, esp32_ip, local_filename="./data/details.json"):
        self.esp32_ip = esp32_ip
        self.local_file = local_filename
        self.url = f"http://{self.esp32_ip}/details"
        self.headers = {'Content-Type': 'application/json'}
        print(f"--- details Manager Initialized for ESP32 at {self.esp32_ip} ---")

    def sync_from_esp32(self):
        """Downloads the details from the ESP32 and replaces the local version."""
        print(f"-> Attempting to GET details from {self.url}...")
        try:
            response = requests.get(self.url, timeout=5)
            response.raise_for_status()
            with open(self.local_file, 'w') as f:
                json.dump(response.json(), f, indent=4)
            print(f"   Success! Synced and saved details to '{self.local_file}'")
            return True
        except requests.exceptions.RequestException as e:
            print(f"   Error: Could not get details from ESP32. {e}")
            return False

    def update_esp32(self):
        """Reads the local details file and pushes it to the ESP32."""
        if not os.path.exists(self.local_file):
            print(f"   Error: Local file '{self.local_file}' not found.")
            return False
        print(f"-> Attempting to POST details to {self.url}...")
        try:
            with open(self.local_file, 'r') as f:
                data = f.read()
                print("To be sent (update_esp32)")
                print(data)
            response = requests.post(self.url, data=data, headers=self.headers, timeout=5)
            response.raise_for_status()
            print("   Success! ESP32 detailsuration updated.")
            print(f"   Server response: {response.text}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"   Error: Could not push details to ESP32. {e}")
            return False

    def get_local_details(self):
        """Reads and returns the local detailsuration as a Python dictionary."""
        try:
            with open(self.local_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"   Error: Could not read local details file: {e}")
            return None

    def save_local_details(self, details_dict):
        """Saves a Python dictionary to the local details file."""
        try:
            with open(self.local_file, 'w') as f:
                json.dump(details_dict, f, indent=4)
            return True
        except Exception as e:
            print(f"   Error: Could not save local details: {e}")
            return False

def run_sync_and_update_cycle(manager:ESP32detailsManager):
    """
    Performs one full cycle of syncing, modifying, and updating the details.
    
    Args:
        manager (ESP32detailsManager): An instance of the details manager.
    """
    details = manager.get_local_details()
    if not details:
        print("--- Cycle Failed: Could not read local details. ---")
        return
        
    manager.update_esp32()


def main():
    """Main function to set up and run the test."""
    ESP32_IP = "192.168.68.184"
    
    # Initialize the manager for the specific ESP32
    details_manager = ESP32detailsManager(ESP32_IP)
    
    # Run the test cycle
    run_sync_and_update_cycle(details_manager)


if __name__ == "__main__":
    main()