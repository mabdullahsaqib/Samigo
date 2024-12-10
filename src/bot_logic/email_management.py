import base64
import os.path
from email.mime.text import MIMEText

import google.generativeai as genai  # Ensure Gemini API client is imported
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import GMAIL_TOKEN_PATH, GEMINI_API_KEY

# Define the Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.send']

# Initialize Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


def authenticate_gmail(command=None, payload=None):
    """
    Authenticates and returns Gmail API service credentials or handles authorization flow.

    Parameters:
    - command (str): The command input from the user, e.g., 'auth_token'.
    - payload (dict): Payload containing data like the token.

    Returns:
    - dict: Response message or status based on the operation.
    """
    creds = None

    # Load existing credentials if available
    if os.path.exists(GMAIL_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_PATH, SCOPES)

    # Refresh or request new credentials if invalid
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif command == "auth_token" and payload and "token" in payload:
            try:
                # Save the token to the credentials file
                token = payload["token"]

                with open(GMAIL_TOKEN_PATH, "w") as token_file:
                    token_file.write(token.to_json())

                return {"status": "success", "message": "Token saved successfully."}
            except Exception as e:
                return {"status": "error", "message": f"Failed to save token: {e}"}
        else:
            return {"status": "auth_required", "message": "No valid token available."}

    return {"status": "success", "creds": creds}


def fetch_emails(service, max_results=5):
    """
    Fetches the most recent emails from the user's inbox.
    Returns a list of email data dictionaries.
    """
    try:
        results = service.users().messages().list(userId='me', maxResults=max_results).execute()
        messages = results.get('messages', [])
        if not messages:
            return []

        emails = []
        for msg in messages:
            message = service.users().messages().get(userId='me', id=msg['id']).execute()
            headers = {header['name']: header['value'] for header in message['payload']['headers']}
            email_data = {
                "id": message['id'],
                "from": headers.get("From", "Unknown Sender"),
                "to": headers.get("To", "Unknown Receiver"),
                "subject": headers.get("Subject", "No Subject"),
                "snippet": message['snippet']
            }
            emails.append(email_data)
        return emails
    except HttpError as error:
        return {"error": str(error)}


def send_email(service, to_email, subject, message_text):
    """
    Sends an email with the specified recipient, subject, and body.
    """
    try:
        message = MIMEText(message_text)
        message['To'] = to_email
        message['Subject'] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        send_message = {'raw': raw_message}
        sent_message = service.users().messages().send(userId='me', body=send_message).execute()
        return {"message": "Message sent", "id": sent_message['id']}
    except HttpError as error:
        return {"error": str(error)}


def summarize_email(service, email_id):
    """
    Summarizes the content of an email by its ID using Gemini.
    Returns the summary text.
    """
    try:
        message = service.users().messages().get(userId='me', id=email_id).execute()
        snippet = message.get('snippet', '')
        summary = model.generate_content(f"Summarize this email: {snippet}")
        return {"summary": summary.text}
    except HttpError as error:
        return {"error": str(error)}


def send_email_with_generated_response(service, email_id):
    """
    Generates and sends a response to an email using Gemini.
    Returns the status of the sent email.
    """
    try:
        message = service.users().messages().get(userId='me', id=email_id).execute()
        snippet = message.get('snippet', '')
        response = model.generate_content(f"Reply to this email: {snippet}")
        headers = {header['name']: header['value'] for header in message['payload']['headers']}
        sender_email = headers.get("From", "Unknown")
        subject = "Re: " + headers.get("Subject", "No Subject")
        return send_email(service, sender_email, subject, response.text)
    except HttpError as error:
        return {"error": str(error)}


def email_voice_interaction(data):
    """
    Handles email commands via voice interaction (from Flask).
    Returns a JSON response with relevant data.
    """

    creds = authenticate_gmail()
    if "status" in creds:
        return creds
    service = build('gmail', 'v1', credentials=creds)

    command = data.get("command", "")
    payload = data.get("payload", {})

    if "fetch" in command:
        emails = fetch_emails(service, 10)
        response = {"emails": emails}

    elif "send" in command:
        to_email = payload.get("to_email", "").strip()
        subject = payload.get("subject", "").strip()
        message_text = payload.get("message_text", "").strip()
        send_result = send_email(service, to_email, subject, message_text)
        response = send_result

    elif "summarize" in command:
        email_id = payload.get("email_id", "").strip()
        summary = summarize_email(service, email_id)
        response = summary

    elif "reply" in command:
        email_id = payload.get("email_id", "").strip()
        send_result = send_email_with_generated_response(service, email_id)
        response = send_result

    else:
        response = {"error": "Command not recognized. Please try again."}

    return response
#
# if __name__ == "__main__":
#     # Test email_voice_interaction function
#     data = {
#         "command": "fetch_emails"
#     }
#     print(email_voice_interaction(data))
