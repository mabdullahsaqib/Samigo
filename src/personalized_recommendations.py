import random
from datetime import datetime, timedelta

import google.generativeai as genai
import pyttsx3
import speech_recognition as sr
from firebase_admin import firestore

from config import GEMINI_API_KEY
from weather_and_news import get_news

# Initialize Firestore
db = firestore.client()

# Initialize Gemini model
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Example categories for recommendations
INTEREST_CATEGORIES = ["technology", "health", "entertainment", "business", "sports"]

# Initialize recognizer and text-to-speech
recognizer = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty('rate', 250)


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


# Store user preferences
def update_preferences(user_id, preference_type, preference):
    doc_ref = db.collection("user_preferences").document(user_id)
    doc = doc_ref.get()
    if doc.exists:
        doc_ref.update({preference_type: preference})
    else:
        doc_ref.set({preference_type: preference})


# Fetch user preferences
def fetch_preferences(user_id):
    doc_ref = db.collection("user_preferences").document(user_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        return {}


# Recommend news based on preferences
def recommend_news(user_id):
    preferences = fetch_preferences(user_id)
    news_category = preferences.get("news_category", random.choice(INTEREST_CATEGORIES))
    return get_news(category=news_category)


# Recommend tasks based on user's activity
def recommend_tasks(user_id):
    doc_ref = db.collection("tasks").where("user_id", "==", user_id).stream()
    tasks = [doc.to_dict() for doc in doc_ref]

    # Filter high-priority or urgent tasks
    recommended_tasks = [
        task for task in tasks if task.get("priority") == "high" or
                                  (task.get("deadline") and datetime.strptime(task["deadline"],
                                                                              "%Y-%m-%d %H:%M") < datetime.now() + timedelta(
                                      days=1))
    ]
    return recommended_tasks if recommended_tasks else ["No urgent tasks!"]


# Recommend general activities (e.g., personalized greetings)
def general_recommendations(user_id):
    preferences = fetch_preferences(user_id)
    if not preferences:
        return "Welcome! Set some preferences to get personalized recommendations."

    # Use Gemini to suggest personalized recommendations
    try:
        response = model.generate_content(
            f"User preferences are: {preferences}. Suggest some activities or recommendations, don't ask any questions.")
        gemini_recommendation = response.text
    except Exception as e:
        gemini_recommendation = f"Could not generate recommendation due to an error: {e}"

    return gemini_recommendation


# Example function to handle voice command input for recommendations
def recommendations_voice_interaction(command):
    user_id = "teuff"
    if "news" in command.lower():
        news = recommend_news(user_id)
        speak("Here are some news articles you might find interesting:")
        for article in news:
            print(article)


    elif "tasks" in command.lower():
        tasks = recommend_tasks(user_id)
        speak("Here are some tasks you should consider completing soon:")
        for task in tasks:
            print(task)


    elif "recommendations" in command.lower() or "personalized" in command.lower() or "recommendation" in command.lower():
        recommendation = general_recommendations(user_id)
        speak(recommendation)

    else:
        return "Sorry, I didn't quite catch that. Please specify if you want news, tasks, or general recommendations."
