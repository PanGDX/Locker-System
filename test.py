import requests
import json

# The URL of your ESP32 server
url = "http://192.168.68.184/"

# The data you want to send (as a Python dictionary)
payload = {
    "device_id": "temp-sensor-01",
    "reading": 25.7,
    "unit": "Celsius"
}

# The headers
headers = {
    "Content-Type": "application/json"
}

try:
    # The requests library formats the HTTP POST request for you
    response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=5)

    # Print the server's response
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")