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
        dict: A dictionary containing the detected language and translated text.
    """
    try:
        # Detect the original language
        detection = translator.detect(text)
        detected_language = detection.lang
        confidence = detection.confidence
        print(f"Detected language: {detected_language} (Confidence: {confidence * 100:.2f}%)")

        # Translate the text to the target language
        translated = translator.translate(text, dest=target_language)
        print(f"Translated to {target_language}: {translated.text}")

        return {
            "detected_language": detected_language,
            "confidence": confidence,
            "translated_text": translated.text
        }
    except Exception as e:
        print(f"Error during translation: {e}")
        return {
            "error": str(e)
        }


def translation_voice_interaction(data):
    """
    Handle translation requests in a structured format.

    Parameters:
        request_data (dict): JSON input with `text` and `target_language`.

    Example Request:
        {
            "text": "Bonjour",
            "target_language": "en"
        }

    Returns:
        dict: JSON response containing detected language, confidence, and translated text.
    """
    try:
        payload = data.get("payload", {})
        text = payload.get("text", "")
        target_language = data.get("target_language", "en")

        if not text:
            return {"error": "No text provided for translation."}

        translation_result = translate_text(text, target_language)
        return translation_result

    except Exception as e:
        return {"error": str(e)}
