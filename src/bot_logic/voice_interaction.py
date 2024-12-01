# Import all the modules as needed
from .interaction_history import handle_user_command
from .task_management import task_voice_interaction
from .web_browsing import web_browsing_voice_interaction
from .note_taking import note_voice_interaction
from .realtime_translation import translation_voice_interaction
from .email_management import email_voice_interaction
from .weather_and_news import weather_and_news_voice_interaction


def activate_module(session_id, command, chat):
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
