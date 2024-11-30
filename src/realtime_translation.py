
from googletrans import Translator


# Initialize the translator
translator = Translator()


def translate_text(text, target_language="en"):
    """
    Translates text to a specified target language.

    Parameters:
        text (str): The text to translate.
        target_language (str): The language code to translate the text to (e.g., "en" for English, "fr" for French).

    Returns:
        str: The translated text.
    """
    try:
        # Detect the original language
        detected_language = translator.detect(text).lang
        print(f"Detected language: {detected_language}")

        # Translate the text to the target language
        translated = translator.translate(text, dest=target_language)
        print(f"Translated to {target_language}: {translated.text}")

        return translated.text

    except Exception as e:
        print(f"Error during translation: {e}")
        return None


def translation_voice_interaction():
    """
    Main function to interact with the Real-Time Translation system.
    It inputs for input in one language and translates it to another language.
    """
    print("Real-Time Translation - Say 'exit' to quit.")

    while True:
        print("\nPlease say something to translate...")
        text_to_translate = input()

        if text_to_translate.lower() == "exit":
            print("Exiting Real-Time Translation.")
            break

        print(f"Original Text: {text_to_translate}")

        # Ask the user for the target language
        target_language = "en"

        translated_text = translate_text(text_to_translate, target_language)
        print("Translated Text : " + translated_text)
        print(translated_text)
