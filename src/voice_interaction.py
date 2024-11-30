import random
import time

import firebase_admin
import pyttsx3
import speech_recognition as sr
from firebase_admin import credentials

from config import FIREBASE_CREDENTIALS_PATH

# Firebase initialization
cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred)

# Import all the modules as needed
# from interaction_history import interaction_history, handle_user_command
# from task_management import task_voice_interaction
from web_browsing import web_browsing_voice_interaction
# from note_taking import note_voice_interaction
# from document_management import document_management_voice_interaction
# from custom_commands import check_and_execute_command
# from realtime_translation import translation_voice_interaction
from email_management import email_voice_interaction
# from weather_and_news import weather_and_news_voice_interaction
# from personalized_recommendations import recommendations_voice_interaction
# from meeting_summaries import meeting_summary_voice_interaction
# from advanced_notfilications import check_and_notify_tasks

# Initialize recognizer and text-to-speech
recognizer = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty('rate', 250)  # Adjust speaking rate if needed

# Initialize chat history
# session_id, chat = interaction_history()

# Constants
INACTIVITY_THRESHOLD = 1800  # 30 minutes in seconds
Entertainment_Commands = ["play", "pause", "stop", "resume", "skip", "next", "previous", "shuffle", "repeat", "look"
                                                                                                              "volume up",
                          "volume down", "increase", "decrease", "seek", "jump"]


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


def activate_module(command):
    """
    Activate the appropriate module based on the user's command.
    """

    response = handle_user_command(session_id, command, chat)

    if "task" in command:
        task_voice_interaction(command)
    elif "web" in command or "search" in command or "browse" in command:
        web_browsing_voice_interaction(command)
    elif "note" in command:
        note_voice_interaction(command)
    elif "document" in command or "file" in command or "folder" in command or "directory" in command or "drive" in command:
        document_management_voice_interaction(command)
    elif "translation" in command or "translate" in command:
        translation_voice_interaction()
    elif "email" in command or "mail" in command or "inbox" in command:
        email_voice_interaction(command)
    elif "weather" in command or "news" in command or "headline" in command or "article" in command:
        weather_and_news_voice_interaction(command)
    elif "recommendation" in command or "suggestion" in command or "advice" in command or "recommendations" in command or "recommend" in command:
        recommendations_voice_interaction(command)
    elif "entertainment" in command or "music" in command or "video" in command or "movie" in command or "spotify" in command or "youtube" in command or any(
            cmd in command for cmd in Entertainment_Commands):
        entertainment_control_voice_interaction(command)
    elif "meeting" in command or "summary" in command or "transcript" in command or "transcribe" in command:
        meeting_summary_voice_interaction(command)
    elif "custom" in command or "execute" in command or "run" in command or "perform" in command or "open" in command or "launch" in command or "start" in command:
        check_and_execute_command(command)
    else:
        print(response)
        speak(response)


def main():
    """
    Main function to handle voice commands and activate modules.
    """
    greetings = ["Hello, how can I assist you today?", "Hi, what can I do for you?", "Hey, how can I help you?",
                 "Greetings, what can I do for you?", "Hello, how can I help you today?"]
    goodbyes = ["See you later!", "Goodbye, have a great day!", "Goodbye, take care!", "Goodbye, see you soon!",
                "Goodbye, have a nice day!"]
    speak(random.choice(greetings))

    # Track last command time
    last_command_time = time.time()

    while True:
        # Check inactivity
        if time.time() - last_command_time >= INACTIVITY_THRESHOLD:
            check_and_notify_tasks()
            # Reset timer after notification
            last_command_time = time.time()

        command = listen()
        if "exit" in command.lower():
            speak(random.choice(goodbyes))
            break
        activate_module(command.lower())


def test_main():
    # email_voice_interaction("fetch emails")
    web_browsing_voice_interaction("Pokemon")


if __name__ == "__main__":
    test_main()
