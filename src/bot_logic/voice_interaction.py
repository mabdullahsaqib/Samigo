# Import all the modules as needed
from .interaction_history import handle_user_command
from .task_management import task_voice_interaction
from .web_browsing import web_browsing_voice_interaction
from .note_taking import note_voice_interaction
from .realtime_translation import translation_voice_interaction
from .email_management import email_voice_interaction
from .weather_and_news import weather_and_news_voice_interaction


def activate_module(session_id, data, chat):
    """
    Activate the appropriate module based on the user's data and return the response.
    """
    # Default response from data history handling
    command = data.get("command", "")
    response = handle_user_command(session_id, command, chat)

    # Determine the module to activate based on keywords in the data
    if "task" in command:
        response = task_voice_interaction(data)
    elif "web" in command or "search" in command or "browse" in command:
        response = web_browsing_voice_interaction(data)
    elif "note" in command:
        response = note_voice_interaction(data)
    elif "translation" in command or "translate" in command:
        response = translation_voice_interaction()
    elif "email" in command or "mail" in command or "inbox" in command:
        response = email_voice_interaction(data)
    elif "weather" in command or "news" in command or "headline" in command or "article" in command:
        response = weather_and_news_voice_interaction(data)

    # Fallback to the default response if no modules are triggered
    return response
