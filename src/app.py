import google.generativeai as genai
from flask import Flask, request, jsonify
from bot_logic.interaction_history import interaction_history
from bot_logic.voice_interaction import activate_module
from bot_logic.config import GEMINI_API_KEY

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
    model_name="genai-1.5-flash",
    generation_config=generation_config,
)

@app.route("/command", methods=['POST'])
def execute_command():
    """Endpoint to execute user commands."""
    try:
        data = request.get_json()
        if not data or "command" not in data:
            return jsonify({"error": "Command is required."}), 400

        raw_command = data["command"].strip()
        print(f"Received command: {raw_command}")

        # Process the command and get a response
        response = activate_module(session_id, raw_command, chat)
        print(f"Response: {response}")

        return jsonify({"response": response}), 200

    except Exception as error:
        print(f"Error occurred: {error}")
        return jsonify({"error": str(error)}), 500

if __name__ == "__main__":
    app.run(debug=True)
