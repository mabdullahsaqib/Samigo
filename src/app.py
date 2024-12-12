import json

import google.generativeai as genai
from flask import Flask, request, jsonify

from bot_logic.config import GEMINI_API_KEY
from bot_logic.interaction_history import interaction_history
from bot_logic.voice_interaction import activate_module

# Initialize Flask app
app = Flask(__name__)

# Initialize chat history
session_id, chat = interaction_history()

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-2.0-flash-exp",
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

    if not data or "command" not in data:
        return jsonify({"error": "Command is required."}), 400

    raw_command = data["command"].strip()
    print(f"Received command: {raw_command}")

    # Retrieve the Bearer token from the Authorization header
    token = get_bearer_token(request)

    parsed_command_response = chat.send_message(f"Now process the following command: {raw_command}"

                                                     )

    try:
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
            except Exception as e:
                return jsonify({"error": f"Failed to execute the command: {e}"}), 404

        if "status" in api_response:
            return jsonify(api_response), 200

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

        return jsonify({"response": natural_response_text}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal server error."}), 500


if __name__ == "__main__":
    app.run(debug=True)
