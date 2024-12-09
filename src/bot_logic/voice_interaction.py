# Import all the modules as needed
from .email_management import email_voice_interaction
from .interaction_history import handle_user_command
from .note_taking import note_voice_interaction
from .realtime_translation import translation_voice_interaction
from .task_management import task_voice_interaction
from .weather_and_news import weather_and_news_voice_interaction
from .web_browsing import web_browsing_voice_interaction


def activate_module(session_id, data, chat):
    """
    Activate the appropriate module based on the user's data and return the response.
    """
    # Default response from data history handling
    module = data.get("module", "")
    response = handle_user_command(session_id, data.get("command", module), chat)

    # Determine the module to activate based on keywords in the data
    if "task" in module or "reminder" in module or "schedule" in module:
        response = task_voice_interaction(data)
    elif "web" in module or "search" in module or "browse" in module or "website" in module:
        response = web_browsing_voice_interaction(data)
    elif "note" in module or "record" in module or "write" in module:
        response = note_voice_interaction(data)
    elif "translation" in module or "translate" in module or "language" in module or "interpret" in module:
        response = translation_voice_interaction(data)
    elif "email" in module or "mail" in module or "inbox" in module:
        response = email_voice_interaction(data)
    elif "weather" in module or "news" in module or "headline" in module or "article" in module or "forecast" in module or "temperature" in module:
        response = weather_and_news_voice_interaction(data)

    # Fallback to the default response if no modules are triggered
    return response
