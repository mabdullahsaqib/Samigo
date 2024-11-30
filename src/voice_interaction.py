import random

import firebase_admin

from firebase_admin import credentials

from config import FIREBASE_CREDENTIALS_PATH

# Firebase initialization
cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred)

# Import all the modules as needed
from interaction_history import interaction_history, handle_user_command
from task_management import task_voice_interaction
from web_browsing import web_browsing_voice_interaction
from note_taking import note_voice_interaction
from realtime_translation import translation_voice_interaction
from email_management import email_voice_interaction
from weather_and_news import weather_and_news_voice_interaction


# Initialize chat history
session_id, chat = interaction_history()


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
    elif "translation" in command or "translate" in command:
        translation_voice_interaction()
    elif "email" in command or "mail" in command or "inbox" in command:
        email_voice_interaction(command)
    elif "weather" in command or "news" in command or "headline" in command or "article" in command:
        weather_and_news_voice_interaction(command)
    else:
        print(response)


def main():
    """
    Main function to handle voice commands and activate modules.
    """
    greetings = ["Hello, how can I assist you today?", "Hi, what can I do for you?", "Hey, how can I help you?",
                 "Greetings, what can I do for you?", "Hello, how can I help you today?"]
    goodbyes = ["See you later!", "Goodbye, have a great day!", "Goodbye, take care!", "Goodbye, see you soon!",
                "Goodbye, have a nice day!"]
    print(random.choice(greetings))

    while True:
        command = input("Please say a command: ")
        if "exit" in command.lower():
            print(random.choice(goodbyes))
            break
        activate_module(command.lower())


if __name__ == "__main__":
    main()
