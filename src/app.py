import json

import google.generativeai as genai
from flask import Flask, request, jsonify

from bot_logic.config import GEMINI_API_KEY
from bot_logic.interaction_history import interaction_history
from bot_logic.voice_interaction import activate_module
from bot_logic.email_management import authenticate_gmail

# Initialize Flask app
app = Flask(__name__)

# Initialize chat history
session_id, chat = interaction_history()

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Set up model configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Initialize the generative AI model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# Function to get the bearer token from the request
def get_bearer_token(request):
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header[7:]  # Extract token
    return None

@app.route("/command", methods=['POST'])
def execute_command():
    """Endpoint to execute user commands."""
    data = request.get_json()

    print(f"Received data: {data}")

    print(f"Request: {request}")

    print(f"Request headers: {request.headers}")
    print(f"Request data: {request.data}")

    if not data or "command" not in data:
        return jsonify({"error": "Command is required."}), 400

    raw_command = data["command"].strip()
    print(f"Received command: {raw_command}")

    # Retrieve the Bearer token from the Authorization header
    token = get_bearer_token(request)
    print(f"Received token: {token}")

    parsed_command_response = model.generate_content(f"""
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

Now process the following command: "{raw_command}"
"""

                                                     )

    try:
        # Generate the content from GeminiF
        print(f"Raw response from Gemini: {parsed_command_response.text}")

        # Clean and parse the JSON
        parsed_command_text = parsed_command_response.text.strip("```").strip("json").strip("\n").strip("```").strip()

        try:
            parsed_command = json.loads(parsed_command_text)
        except json.JSONDecodeError as e:
            return jsonify({"error": f"Failed to parse the command: {e}"}), 400

        print(f"Parsed command: {parsed_command}")
        if parsed_command["module"] == "":
            api_response = parsed_command["message"]
            print(f"API response: {api_response}\n")
            return jsonify({"response": api_response}), 200
        else:
            try:
                api_response = activate_module(session_id, parsed_command, chat, token)
                print(f"API response: {api_response}\n")
            except Exception as e:
                return jsonify({"error": f"Failed to execute the command: {e}"}), 404

        # print(f"API response: {api_response}\n")

        if "status" in api_response:
            return jsonify(api_response), 200

        # if "error" in api_response:
        #    return jsonify({"error": "Invalid command"}), 400
        # else:
        natural_response = model.generate_content(f"""
            You are a natural language processing model tasked with converting structured data output into natural language responses. Your goal is to generate user-friendly, conversational outputs that explain the results of various actions performed on different modules. 
            
            Here are the modules and the corresponding structured output you will convert into natural language:
            
            1. **Task Management Module**:
                - Commands: "add", "priority", "category", "upcoming", "delete"
                - Example Output:
                    - For "add": {{ "status": "success", "task": {{ "description": "Finish report", "deadline": "next Monday" }} }}
                    - For "priority": {{ "tasks": [ {{ "title": "Finish report", "priority": "high", "deadline": "next Monday" }}, ... ] }}
                    - For "category": {{ "tasks": [ {{ "title": "Finish report", "category": "work", "deadline": "next Monday" }}, ... ] }}
                    - For "upcoming": {{ "tasks": [ {{ "title": "Finish report", "deadline": "next Monday" }}, ... ] }}
                    - For "delete": {{ "status": "success", "message": "Task 'Buy groceries' deleted successfully." }}
                - Output Format:
                    - "Task added successfully: '{{task_description}}', due by {{deadline}}."
                    - "Here are your {{priority}} priority tasks:"
                    - "You have {{num_tasks}} tasks in the {{category}} category."
                    - "The following tasks are due by {{deadline}}:"
                    - "Task '{{task_title}}' has been deleted successfully."
            
            2. **Web Browsing Module**:
                - Commands: "search", "summarize"
                - Example Output:
                    - For "search": {{ "results": [ {{ "title": "AI in Healthcare", "link": "https://example.com" }}, ... ] }}
                    - For "summarize": {{ "summary": "Artificial intelligence is transforming healthcare..." }}
                - Output Format:
                    - "Here are the top search results for '{{query}}':"
                    - "Summary of the search results: {{summary}}"
            
            3. **Note Management Module**:
                - Commands: "add", "retrieve", "summarize", "delete", "edit"
                - Example Output:
                    - For "add": {{ "status": "success", "note": {{ "title": "Meeting Notes", "content": "Discussed project updates" }} }}
                    - For "retrieve": {{ "notes": [ {{ "title": "Meeting Notes", "content": "Discussed project updates" }}, ... ] }}
                    - For "summarize": {{ "summary": "Discussed project updates..." }}
                    - For "delete": {{ "status": "success", "message": "Note 'Meeting Notes' deleted successfully." }}
                    - For "edit": {{ "status": "success", "message": "Note 'Meeting Notes' updated successfully." }}
                - Output Format:
                    - "Note '{{note_title}}' added successfully."
                    - "Here are your notes containing '{{keyword}}':"
                    - "Summary of note '{{note_title}}': {{summary}}"
                    - "Note '{{note_title}}' deleted successfully."
                    - "Note '{{note_title}}' has been updated successfully."
            
            4. **Translation Module**:
                - Commands: "translate"
                - Example Output:
                    - For "translate": {{ "translated_text": "Hello, how are you?" }}
                - Output Format:
                    - "The translation of '{{text}}' to {{target_language}} is: {{translated_text}}"
            
            5. **Weather and News Module**:
                - Commands: "weather", "news"
                - Example Output:
                    - For "weather": {{ "location": "Paris", "temperature": "18°C", "condition": "sunny", "humidity": "60%", "wind_speed": "15 km/h" }}
                    - For "news": {{ "articles": [ {{ "title": "AI in Healthcare", "description": "AI is transforming healthcare..." }}, ... ] }}
                - Output Format:
                    - "The weather in {{location}} is {{temperature}}, with {{condition}}. Humidity is {{humidity}}% and wind speed is {{wind_speed}}."
                    - "Here are the top {{num_articles}} news headlines:"
                    - "{{article_title}}: {{article_description}}"
            
            6. **Email Management Module**:
                - Commands: "fetch", "send", "summarize", "reply"
                - Example Output:
                    - For "fetch": {{ "emails": [ {{ "subject": "Meeting", "from": "john@example.com" }}, ... ] }}
                    - For "send": {{ "status": "success", "message": "Email sent successfully to {{to_email}}" }}
                    - For "summarize": {{ "summary": "Meeting with John about the new project." }}
                    - For "reply": {{ "status": "success", "message": "Reply sent to email ID {{email_id}}" }}
                - Output Format:
                    - "You have {{num_emails}} new emails."
                    - "Email sent successfully to {{to_email}} with subject '{{subject}}'."
                    - "Summary of the email: {{summary}}"
                    - "Reply sent to email ID {{email_id}}."
            
            ### Task:
            Please convert the structured output data into natural language responses that can be easily understood by users.
            
            ### Example Input and Output:
            
            1. **Input**: {{ "status": "success", "task": {{ "description": "Finish report", "deadline": "next Monday" }} }}
                - **Output**: "Task added successfully: 'Finish report', due by next Monday."
            
            2. **Input**: {{ "results": [ {{ "title": "AI in Healthcare", "link": "https://example.com" }} ] }}
                - **Output**: "Here are the top search results for 'AI in Healthcare':\n1. AI in Healthcare - [Link](https://example.com)"
            
            3. **Input**: {{ "notes": [ {{ "title": "Meeting Notes", "content": "Discussed project updates" }} ] }}
                - **Output**: "Here are your notes containing 'project':\n1. Meeting Notes: Discussed project updates"
            
            4. **Input**: {{ "translated_text": "Hello, how are you?" }}
                - **Output**: "The translation of 'Hola, ¿cómo estás?' to English is: Hello, how are you?"
            
            5. **Input**: {{ "location": "Paris", "temperature": "18°C", "condition": "sunny", "humidity": "60%", "wind_speed": "15 km/h" }}
                - **Output**: "The weather in Paris is 18°C, with sunny conditions. Humidity is 60% and wind speed is 15 km/h."
            
            6. **Input**: {{ "emails": [ {{ "subject": "Meeting", "from": "john@example.com" }} ] }}
                - **Output**: "You have 1 new email.\nSubject: Meeting\nFrom: john@example.com"
            
            7. **Input**: {{ "status": "success", "message": "Email sent successfully to john.doe@example.com" }}
                - **Output**: "Email sent successfully to john.doe@example.com."
            
            8. **Input**: {{ "summary": "AI in healthcare is improving patient outcomes and streamlining medical processes." }}
                - **Output**: "Summary of the search results: AI in healthcare is improving patient outcomes and streamlining medical processes."
            
            9. **Input**: {{ "status": "success", "message": "Task 'Buy groceries' deleted successfully." }}
                - **Output**: "Task 'Buy groceries' has been deleted successfully."
            
            10. **Input**: {{ "summary": "Discussed project updates with the team. Everyone is on track for deadlines." }}
                - **Output**: "Summary of note 'Meeting Notes': Discussed project updates with the team. Everyone is on track for deadlines."
            
            11. **Input**: {{ "location": "New York City", "temperature": "10°C", "condition": "cloudy", "humidity": "75%", "wind_speed": "20 km/h" }}
                - **Output**: "The weather in New York City is 10°C, with cloudy conditions. Humidity is 75% and wind speed is 20 km/h."
            
            12. **Input**: {{ "status": "success", "message": "Note 'Meeting Notes' updated successfully." }}
                - **Output**: "Note 'Meeting Notes' has been updated successfully."
            
            13. **Input**: {{ "summary": "Project updates discussed, deadlines confirmed." }}
                - **Output**: "Summary of note 'Project Meeting': Project updates discussed, deadlines confirmed."
            
            14. **Input**: {{ "status": "success", "message": "Reply sent to email ID 12345" }}
                - **Output**: "Reply sent to email ID 12345."
            
             ---            

            ### Inputs:
            **Raw Command**: "{raw_command}"
            **API Response**: {api_response}

            ### Answer:
        """)

        natural_response_text = natural_response.text.strip()
        print(f"Natural language response: {natural_response_text}")

        return jsonify({"response": natural_response_text}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal server error."}), 500


if __name__ == "__main__":
    app.run(debug=True)
