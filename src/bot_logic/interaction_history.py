from datetime import datetime

import google.generativeai as genai
from firebase_admin import firestore

from .config import GEMINI_API_KEY
# Initialize Firestore
from .firebase_initializer import db

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
    print(f"Session ID: {session_id}")
    response = chat.send_message("""
        Extract the required information from the following command and return a dictionary. The dictionary keys should match the expected fields for the Samigo Bot API commands, and the values should be extracted or inferred from the command. If a value is missing in the command, leave it.
        Look out for any grammatical errors in the raw command and assume the correct word.

            Here are the modules and their expected data inputs:

            1. **Task Management Module**:
                - Commands: "add", "priority", "category", "upcoming", "delete"
                - Expected Payload: 
                    - For "add": {{"description": string, "deadline": string (optional) }}
                    - For "priority": {{"priority": string (e.g., "high", "medium", "low") }}
                    - For "category": {{"category": string (e.g., "work", "personal") }}
                    - For "upcoming": {{"deadline": string (optional) }}
                    - For "delete": {{"title": string }}

            2. **Web Browsing Module**:
                - Commands: "search", "summarize"
                - Expected Payload:
                    - For "search": {{"query": string, "action": string ("summarize" if needed) }}

            3. **Note Management Module**:
                - Commands: "add", "retrieve", "summarize", "delete", "edit"
                - Expected Payload:
                    - For "add": {{"title": string, "content": string, "tags": list (optional) }}
                    - For "retrieve": {{"note_id": string (optional), "keyword": string (optional), "tag": string (optional), "date_range": string (optional) }}
                    - For "summarize": {{"note_id": string }}
                    - For "delete": {{"note_id": string }}
                    - For "edit": {{"note_id": string, "new_title": string, "new_content": string, "new_tags": list (optional) }}

            4. **Translation Module**:
                - Commands: "translate"
                - Expected Payload:
                    - For "translate": {{"text": string, "target_language": string (optional, default is "en") }}

            5. **Weather and News Module**:
                - Commands: "weather", "news"
                - Expected Payload:
                    - For "weather": {{"location": string (default is "Zurich") }}
                    - For "news": {{"category": string (e.g., "general", "business", etc.) }}

            6. **Email Management Module**:
                - Commands: "fetch", "send", "summarize", "reply"
                - Expected Payload:
                    - For "fetch": no additional data required 
                    - For "send": {{"to_email": string, "subject": string, "message_text": string }}
                    - For "summarize": {{"email_id": string }}
                    - For "reply": {{"email_id": string }}

            ### Task:
            Please parse the user's natural language command and return a dictionary with the following structure:
            {{
        "module": string (e.g., "task", "web", "note", "translate", "weather", "news", "email"),
              "command": string (specific command like "add", "fetch", "send", "weather"),
              "payload": specific parameters required for the module and command as described above
            }}
            The "module" indicates which module the command belongs to (task management, web browsing, etc.), "command" specifies the action to be performed, and "payload" contains the necessary data.

            Please handle the natural language input and parse it accordingly. If the command is invalid or unclear, respond with a message indicating that the command is not recognized.

            ### Example Input and Output:

            1. **Command**: "Add a task with the description 'Finish report' and set the deadline to next Monday."
                - **Parsed Output**: 
                ```json
                {{
        "module": "task",
                  "command": "add",
                  "payload": {{
        "description": "Finish report",
                    "deadline": "next Monday"
                  }}
                }}
                ```

            2. **Command**: "Show me the latest weather in Paris."
                - **Parsed Output**:
                ```json
                {{
        "module": "weather",
                  "command": "weather",
                  "payload": {{
        "location": "Paris"
                  }}
                }}
                ```

            3. **Command**: "Please send an email to john.doe@example.com with the subject 'Meeting' and message 'Let's meet tomorrow'."
                - **Parsed Output**:
                ```json
                {{
        "module": "email",
                  "command": "send",
                  "payload": {{
        "to_email": "john.doe@example.com",
                    "subject": "Meeting",
                    "message_text": "Let's meet tomorrow"
                  }}
                }}
                ```

            4. **Command**: "Get me the top 5 news headlines in the business category."
                - **Parsed Output**:
                ```json
                {{
        "module": "news",
                  "command": "news",
                  "payload": {{
        "category": "business"
                  }}
                }}
                ```

            5. **Command**: "'Hola, ¿cómo estás?'"
                - **Parsed Output**:
                ```json
                {{
        "module": "translate",
                  "command": "translate",
                  "payload": {{
        "text": "Hola, ¿cómo estás?",
                    "target_language": "en"
                  }}
                }}
                ```

            6. **Command**: "Please add a note titled 'Meeting Notes' with the content 'Discussed project updates' and tagged 'work'."
                - **Parsed Output**:
                ```json
                {{
        "module": "note",
                  "command": "add",
                  "payload": {{
        "title": "Meeting Notes",
                    "content": "Discussed project updates",
                    "tags": ["work"]
                  }}
                }}
                ```

            7. **Command**: "Show me notes about 'project' from last week."
                - **Parsed Output**:
                ```json
                {{
        "module": "note",
                  "command": "retrieve",
                  "payload": {{
        "keyword": "project",
                    "date_range": "last week"
                  }}
                }}
                ```

            8. **Command**: "Summarize the email with ID 12345."
                - **Parsed Output**:
                ```json
                {{
        "module": "email",
                  "command": "summarize",
                  "payload": {{
        "email_id": "12345"
                  }}
                }}
                ```

            9. **Command**: "Delete the task titled 'Buy groceries'."
                - **Parsed Output**:
                ```json
                {{
        "module": "task",
                  "command": "delete",
                  "payload": {{
        "title": "Buy groceries"
                  }}
                }}
                ```

            10. **Command**: "Fetch emails from my inbox."
                - **Parsed Output**:
                ```json
                {{
        "module": "email",
                  "command": "fetch",
                  "payload": {{}} 
                }}
                ```

            11. **Command**: "Show me the weather forecast for New York City tomorrow."
                - **Parsed Output**:
                ```json
                {{
        "module": "weather",
                  "command": "weather",
                  "payload": {{
        "location": "New York City"
                  }}
                }}
                ```

            12. **Command**: "Summarize the web search results about 'artificial intelligence'."
                - **Parsed Output**:
                ```json
                {{
        "module": "web",
                  "command": "summarize",
                  "payload": {{
        "query": "artificial intelligence",
                    "action": "summarize"
                  }}
                }}
                ```

            13. **Command**: "Translate 'Bonjour' into Spanish."
                - **Parsed Output**:
                ```json
                {{
        "module": "translate",
                  "command": "translate",
                  "payload": {{
        "text": "Bonjour",
                    "target_language": "es"
                  }}
                }}
                ```

            14. **Command**: "Add a high-priority task to finish the report by Friday."
                - **Parsed Output**:
                ```json
                {{
        "module": "task",
                  "command": "priority",
                  "payload": {{
        "priority": "high"
                  }}
                }}
                ```

            15. **Command**: "Fetch the top news in technology."
                - **Parsed Output**:
                ```json
                {{
        "module": "news",
                  "command": "news",
                  "payload": {{
        "category": "technology"
                  }}
                }}
                ```

        If no module is selected, reply to the message as a conversational chat message :

            16. **Command**: "Hello, how are you today?"
                - **Parsed Output**:
                ```json
                {{
           "module": "", 
        "message":  (reply to the message)
                    }}
                    ```




    Only provide the dictionary in the response. nothing more, nothing less. Don't even write anything or before the brackets.

        """)
    print(f"Start: {response.text}")
    return session_id, chat

# if __name__ == "__main__":
#     session_id, chat = interaction_history()
#     print(f"Session ID: {session_id}")
#     print("Aura: Hello! How can I help you today?")
#     start =
#     print(f"Start: {start}")
#     print(f"Aura: {start.text}")
#     while True:
#         user_input = input("User: ")
#         if user_input.lower() == "exit":
#             break
#         response = handle_user_command(session_id, user_input, chat)
#         print(f"Aura: {response}")