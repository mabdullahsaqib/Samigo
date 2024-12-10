import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Constants (modify these as per your setup)
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']  # Adjust scopes if needed
GMAIL_TOKEN_PATH = "path_to_save_gmail_token.json"  # Update the path as needed


def authenticate_gmail(command=None, payload=None):
    """
    Authenticates and returns Gmail API service credentials or handles authorization flow.

    Parameters:
    - command (str): The command input from the user, e.g., 'auth_token'.
    - payload (dict): Payload containing data like the token.

    Returns:
    - dict: Response message or credentials based on the operation.
    """
    creds = None

    # Check for valid command and payload
    if command == "auth_token" and payload and "token" in payload:
        try:
            # Extract the access token
            access_token = payload["token"]

            # Construct credentials object from access token
            creds = Credentials(token=access_token)

            # Save the token for future use (optional)
            with open(GMAIL_TOKEN_PATH, "w") as token_file:
                token_file.write(creds.to_json())

            return {"status": "success", "creds": creds, "message": "Token authenticated and saved."}

        except Exception as e:
            return {"status": "error", "message": f"Error during authentication: {e}"}

    # Check for existing credentials if no token is provided
    if os.path.exists(GMAIL_TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_PATH, SCOPES)

            # Refresh if credentials are expired
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())

            if creds and creds.valid:
                return {"status": "success", "creds": creds}
        except Exception as e:
            return {"status": "error", "message": f"Failed to load or refresh credentials: {e}"}

    # If no valid credentials are available
    return {"status": "auth_required", "message": "Valid credentials are required."}


# Simulated payload from the frontend
payload = {
    "token": "ya29.a0AeDClZCV8M6u5XsGt7qjHNuCDU2WIaN2dF6fZYPO8ce41qYpPRn4OH3cPhkDKmOYLTRyOjzyCYmbiNWK1qwhcxe7TpUFN74KP2DZSqPmTRwH3sQSsdvpC9qlbCjx8AhvTTwqwE4D8yOpS0ZxDg39Z6ZuNyC8PwejS0ipoTGfaCgYKAdsSARMSFQHGX2MiOO_JljvdpTnbjyBpBGwtqw0175"
}

response = authenticate_gmail(command="auth_token", payload=payload)
if response["status"] == "success":
    creds = response["creds"]
    print("Credentials are ready to use!")
else:
    print(response["message"])
