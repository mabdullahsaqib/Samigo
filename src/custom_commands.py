import subprocess

import google.generativeai as genai
import pyttsx3
import speech_recognition as sr
from firebase_admin import firestore

from config import GEMINI_API_KEY

# Initialize recognizer and text-to-speech
recognizer = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty('rate', 250)  # Adjust speaking rate if needed

# Firebase initialization
db = firestore.client()

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


def speak(text):
    engine.say(text)
    engine.runAndWait()


def listen():
    with sr.Microphone() as source:
        while True:
            print("Listening...")
            audio = recognizer.listen(source)
            try:
                command = recognizer.recognize_google(audio)
                print("Command : " + command)
                return command
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except sr.RequestError:
                speak("Voice service unavailable.")
                return ""


def check_and_execute_command(command_name):
    """
    Checks if a command exists. If not, prompts user to create it,
    generates code suggestions with Gemini, and stores the command.
    """
    command_ref = db.collection("custom_commands").document(command_name)
    command_doc = command_ref.get()

    # Step 1: Check if the command exists
    if command_doc.exists:
        # Execute existing command
        command_action = command_doc.to_dict()["action"]
        subprocess.run(command_action, shell=True)
        speak(f"Executed existing command '{command_name}'.")
    else:
        # Step 2: Prompt user to define new command
        speak(f"The command '{command_name}' does not exist. Would you like to create it?")
        user_confirm = listen()

        if user_confirm and "yes" in user_confirm:
            # Step 3: Get command description from the user
            speak(f"Please assign a command name.")
            command_name = listen()
            speak(f"Please describe what '{command_name}' should do.")
            command_description = listen()

            if command_description:
                try:
                    # Step 4: Pass command description to Gemini
                    gemini_response = model.generate_content(
                        "Suggest a command that can be executed in shell and perform this action : " + command_description + "\nOnly write the command and nothing else. not even quotation marks or endline characters.")
                    suggested_command = gemini_response.text.strip()
                except Exception as e:
                    speak(f"Error generating command suggestion: {e}")
                    return None

                # Confirm the suggested command with the user
                speak(f"Suggested command: {suggested_command}")
                speak("Would you like to save this command?")
                final_confirm = listen()

                if final_confirm and "yes" in final_confirm:
                    # Step 5: Store the new command in Firestore
                    command_ref.set({
                        "action": suggested_command
                    })
                    speak(f"Custom command '{command_name}' added successfully and ready for use.")
                else:
                    speak("Command creation canceled.")
        else:
            speak("Command creation canceled.")
