from datetime import datetime

import google.generativeai as genai
from firebase_admin import firestore

from config import GEMINI_API_KEY

# Initialize Firestore
db = firestore.client()

# Configure GEMINI API
genai.configure(api_key=GEMINI_API_KEY)


# Function to get and increment session ID
def get_next_session_id():
    """
    Retrieve and increment the session ID from a dedicated counter document in Firestore.
    """
    counter_ref = db.collection("metadata").document("session_counter")
    counter_doc = counter_ref.get()
    current_id = counter_doc.to_dict().get("count", 0) if counter_doc.exists else 0
    next_id = current_id + 1
    counter_ref.set({"count": next_id})  # Update the counter in Firestore
    return next_id  # Use plain numeric ID


# Retrieve Latest Session's History by ID
def get_last_session_history():
    """
    Retrieve the chat history from the latest session in Firestore.
    """
    # Fetch the latest session document by ordering by ID in descending order
    sessions = db.collection("interaction_history").order_by("__name__", direction=firestore.Query.DESCENDING).limit(
        1).stream()
    history = []

    # Get messages from the latest session
    for session in sessions:
        messages = session.to_dict().get("messages", [])
        for message in messages:
            if "command" in message and "response" in message:
                history.append({"role": "user", "parts": message["command"]})
                history.append({"role": "model", "parts": message["response"]})

    # print("Retrieved history:", history)
    return history


# GEMINI Interaction with History
def initialize_chat_with_gemini(history):
    model = genai.GenerativeModel("gemini-1.5-flash")
    chat = model.start_chat(history=history)
    return chat


# Save or Append to Continuous Chat in Firestore
def save_to_chat(session_id: int, command: str, response: str):
    chat_ref = db.collection("interaction_history").document(str(session_id))  # Use numeric ID as string
    new_message = {"timestamp": datetime.now(), "command": command, "response": response}
    chat_ref.set({"messages": firestore.ArrayUnion([new_message])}, merge=True)


# Main Interaction Function
def handle_user_command(session_id: int, command: str, chat):
    response = chat.send_message(command)
    save_to_chat(session_id, command, response.text)
    # print(f"Aura: {response.text}")
    return response.text


def interaction_history():
    # Initialize chat history
    session_id = get_next_session_id()
    history = get_last_session_history()
    chat = initialize_chat_with_gemini(history)
    return session_id, chat
