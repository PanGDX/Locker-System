import os
import msal
import requests
import json
from dotenv import load_dotenv
from PyQt6.QtWidgets import QWidget, QMessageBox

load_dotenv()

CLIENT_ID = os.getenv("APPLICATION_CLIENT_ID")
if not CLIENT_ID:
    raise ValueError("APPLICATION_CLIENT_ID not found in environment variables. Please set it in your .env file.")

AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["Mail.Send", "User.Read"]  # Include all necessary scopes
CACHE_FILENAME = "token_cache.bin"


def send_automated_email( parent:QWidget | None,
                         recipient_email:str, 
                         job_number:int, 
                         locker_number:int, 
                         locker_password:int):
    """
    Sends an automated email using the information given
    All errors are printed on the command line and also displayed using the GUI

    Parameters:
        parent => QWidget | None
            Pass the GUI's self into this
        recipient_email => str
            Pass the student's email. Not exclusive to u.nus.edu
        job_number => int
            Example: 2510019
            For formatting and replying to email
        locker_number => int
        locker_password => int

    Output:
        True if the email is successfully sent (code 202)
        False if there is any errors
    """
    cache = msal.SerializableTokenCache()
    if os.path.exists(CACHE_FILENAME):
        with open(CACHE_FILENAME, "r") as f:
            cache.deserialize(f.read())

    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY, token_cache=cache)


    result = None
    accounts = app.get_accounts()
    if accounts:
        print("Account(s) found in cache. Trying to acquire token silently.")
        result = app.acquire_token_silent(SCOPES, account=accounts[0])


    if not result:
        print("No suitable token in cache. Initiating interactive login.")
        QMessageBox.information(parent, "Interactive Login", "o suitable token in cache. Initiating interactive login. Please ensure the wifi is on")
        result = app.acquire_token_interactive(scopes=SCOPES)

    if "access_token" in result:
        print("Login successful!")
        QMessageBox.information(parent, "Login successful", "Login successful")
        

        with open(CACHE_FILENAME, "w") as f:
            f.write(cache.serialize())
        print(f"Token cache has been saved to {CACHE_FILENAME}.")

        access_token = result['access_token']
        endpoint = "https://graph.microsoft.com/v1.0/me/sendMail"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

        email_payload = {
            "message": {
                "subject": f"Collection of {job_number}",
                "body": {
                    "contentType": "HTML", 
                    "content": f"""
Your parts are ready to be collected at the HUB's Locker (directly outside the glass windows) at any time!

Your locker number is: {locker_number}
Your locker password is: {locker_password}
                    """.strip()
                },
                "toRecipients": [{"emailAddress": {"address": recipient_email}}] # <-- CHANGE THIS
            },
            "saveToSentItems": "true"
        }

        response = requests.post(endpoint, headers=headers, data=json.dumps(email_payload))

        if response.status_code == 202:
            print("Email sent successfully!")
            return True
        else:
            QMessageBox.information(parent, "Email Error!", response.json())
            print(f"Error sending email: {response.status_code}")
            print(response.json())
            return False

    else:
        print("Login failed.")
        print(result.get("error"))
        print(result.get("error_description"))
        return False
    
if __name__ == '__main__':
    send_automated_email()