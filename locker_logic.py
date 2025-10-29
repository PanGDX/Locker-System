import json
import os
import random
import string

# Define the path to the local data file.
# The GUI and Bluetooth service will use this path.
DATA_FILE = './data/details.json'


"""
We only need these three functions because locker_logic does not interact with the WIFI module. It solely deal with the 
logic of properly maintaining json file in the local machine. As such it is only concerned with whether the locker is occupied
or not, NOT with whether the mechanism is locked or not. 
"""


def get_all_locker_states() -> dict[str, bool]:
    """
    Reads the data file and returns a dictionary of locker states.

    This function is used to determine the initial display of the lockers
    (e.g., red for occupied, green for available).

    Returns:
        A dictionary where keys are locker IDs and values are booleans
        (True if occupied, False otherwise).
        Returns an empty dictionary if the file doesn't exist or is invalid.
    """
    try:
        # If the file doesn't exist, create it with an empty JSON object
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'w') as f:
                json.dump({}, f)
            return {}
            
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
        
        # Create a simple dictionary { "locker_id": is_occupied }
        return {locker_id: info.get('occupied', False) for locker_id, info in data.items()}

    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error reading locker states from '{DATA_FILE}': {e}")
        # In case of an error, assume no lockers are occupied.
        return {}

def assign_locker(locker_id: str, job_number: str, passcode: str) -> str | None:
    """
    Assigns a locker to a user, generates a passcode, and updates the data file.

    Args:
        locker_id: The ID of the locker to be assigned.
        name: The full name of the user.
        email: The email address of the user.

    Returns:
        The newly generated 6-digit passcode as a string if successful.
        None if there was an error.
    """
    try:
        # Generate a random 6-digit passcode
        # passcode = ''.join(random.choices(string.digits, k=6))
        
        # Read the current data
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # If file is missing or corrupt, start with a fresh dictionary
            data = {}
            
        # Add or update the locker's information
        data[locker_id] = {
            "jobid": job_number,
            "passcode": passcode
        }
        
        # Write the updated data back to the file with pretty printing
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
            
        print(f"Locker {locker_id} assigned to {job_number}. Passcode: {passcode}")
        return passcode

    except IOError as e:
        print(f"Error assigning locker in '{DATA_FILE}': {e}")
        return None

def release_locker(locker_id: str) -> bool:
    """
    Releases a locker, clearing its data from the file.
    NOTE: THIS CLEARS DATA FROM FILE


    This is used both for unlocking a locker and for rolling back a
    failed submission process.

    Args:
        locker_id: The ID of the locker to release.

    Returns:
        True if the locker was successfully released.
        False if the locker was not found or an error occurred.
    """
    try:
        # Read the current data
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            
        # Check if the locker exists in the data
        if locker_id in data:
            # Remove the locker's entry
            del data[locker_id]
            
            # Write the updated data back to the file
            with open(DATA_FILE, 'w') as f:
                json.dump(data, f, indent=4)
            
            print(f"Locker {locker_id} has been released.")
            return True
        else:
            # The locker was not in the file, so there was nothing to do.
            print(f"Warning: Tried to release locker {locker_id}, but it was not found in the data file.")
            return False # Or True, depending on desired behavior for non-existent lockers

    except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
        print(f"Error releasing locker in '{DATA_FILE}': {e}")
        return False
    

