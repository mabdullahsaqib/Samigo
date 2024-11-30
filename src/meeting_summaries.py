import os
from pathlib import Path

import google.generativeai as genai
import pyttsx3
import speech_recognition as sr
import whisper
from firebase_admin import firestore

from config import GEMINI_API_KEY

# Initialize recognizer and text-to-speech
recognizer = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty('rate', 250)  # Adjust speaking rate if needed

# Initialize Firestore
db = firestore.client()

# Initialize GEMINI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


# Initialize Whisper Model
def load_model():
    whisper_model = whisper.load_model("base")
    return whisper_model


# Transcribe Audio Function
def transcribe_audio(whisper_model, file_path):
    result = whisper_model.transcribe(file_path)
    transcript = result['text']
    print("Transcript : ", transcript)
    return transcript


# Summarize Transcript with GEMINI
def summarize_text(text):
    response = model.generate_content("Summarize the following meeting transcript, briefly :" + text)
    print("Summary : ", response.text)
    return response.text


# Store Meeting Summary in Firestore
def store_summary(meeting_title, transcript, summary):
    doc_ref = db.collection("meeting_summaries").document(meeting_title)
    doc_ref.set({
        "title": meeting_title,
        "transcript": transcript,
        "summary": summary
    })
    print(f"Meeting '{meeting_title}' summary saved successfully.")


# Main Function to Transcribe, Summarize, and Store
def process_meeting_summary(file_path, meeting_title):
    whisper_model = load_model()
    print("Transcribing audio...")
    transcript = transcribe_audio(whisper_model, file_path)
    print("Transcription complete. Summarizing text...")
    try:
        summary = summarize_text(transcript)
        print("Summary complete. Storing in Firestore...")
        store_summary(meeting_title, transcript, summary)
        with open(f"{meeting_title}_summary.txt", "w") as file:
            file.write("Summary : " + summary)
        print(f"Meeting summary for '{meeting_title}' processed and stored.")
    except Exception as e:
        print(f"Error occurred : {e}")


def findfile(name, path):
    """Searches for a file by name in a specified base directory."""
    for dirpath, _, filenames in os.walk(path):
        for filename in filenames:
            if Path(filename).stem.lower() == name:
                return Path(dirpath) / filename

    print(f"File '{name}' not found in '{path}'.")
    return None


def getmeetings():
    meetings = db.collection("meeting_summaries").stream()
    for meeting in meetings:
        print(meeting.to_dict())


def retrieve_a_meeting(title):
    doc_ref = db.collection("meeting_summaries").document(title)
    doc = doc_ref.get()
    if doc.exists:
        print(doc.to_dict())
    else:
        print(f"Meeting '{title}' not found in Firestore.")


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


def meeting_summary_voice_interaction(command):
    """
    Handles the meeting summary command.
    Asks user for the audio file and processes the meeting summary.
    """

    if "list" in command or "all" in command:
        speak("Retrieving all meeting summaries from Firestore.")
        getmeetings()
        return
    elif "retrieve" in command or "get" in command:
        speak("Please provide the title of the meeting summary you would like to retrieve.")
        title = listen()
        retrieve_a_meeting(title)
        return
    else:
        speak("What's the name of the audio file? ")
        audio_file = listen()
        audio_file = findfile(audio_file, "C:/Meetings")
        audio_file = str(audio_file).replace("\\", "/")
        if audio_file:
            speak(f"Processing the meeting summary from the file located at {audio_file}.")
            title = Path(audio_file).stem
            process_meeting_summary(audio_file, title)
            speak("The meeting summary has been processed and stored.")
        else:
            speak("Sorry, I couldn't process the audio file. Please try again.")
