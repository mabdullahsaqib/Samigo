import pyttsx3
import requests
import speech_recognition as sr

from config import WEATHER_API_KEY, WEATHER_API_HOST, NEWS_API_KEY

# Initialize recognizer and text-to-speech
recognizer = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty('rate', 250)  # Adjust speaking rate if needed

# Weather API setup
WEATHER_API_URL = "https://weatherapi-com.p.rapidapi.com/current.json"

# News API setup
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"


# Weather fetching function
def get_weather(location):
    querystring = {"q": location}
    headers = {
        "x-rapidapi-key": WEATHER_API_KEY,
        "x-rapidapi-host": WEATHER_API_HOST
    }

    try:
        response = requests.get(WEATHER_API_URL, headers=headers, params=querystring)
        response.raise_for_status()
        data = response.json()

        location_name = data['location']['name']
        country = data['location']['country']
        temp_c = data['current']['temp_c']
        condition = data['current']['condition']['text']
        humidity = data['current']['humidity']
        wind_kph = data['current']['wind_kph']

        return {
            "location": f"{location_name}, {country}",
            "temperature": temp_c,
            "condition": condition,
            "humidity": humidity,
            "wind_speed": wind_kph
        }

    except requests.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None


# News fetching function
def get_news(country="us", category="general", num_articles=5):
    params = {
        "country": country,
        "category": category,
        "pageSize": num_articles,
        "apiKey": NEWS_API_KEY
    }

    try:
        response = requests.get(NEWS_API_URL, params=params)
        response.raise_for_status()
        news_data = response.json()

        articles = news_data.get('articles', [])
        news_summaries = []
        for article in articles:
            news_summaries.append({"title": article['title'], "description": article['description']})

        return news_summaries

    except requests.RequestException as e:
        print(f"Error fetching news data: {e}")
        return None


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


# Function to handle voice commands for Weather and News
def weather_and_news_voice_interaction(command):
    if "weather" in command:
        weather_info = get_weather("Canada")
        if weather_info:
            speak(
                f"The weather in {weather_info['location']} is {weather_info['temperature']} degrees Celsius, {weather_info['condition']}.")
            speak(
                f"The humidity is {weather_info['humidity']}%, and the wind speed is {weather_info['wind_speed']} kilometers per hour.")
        else:
            speak("Sorry, I couldn't fetch the weather information.")

    elif "news" in command:
        speak("Fetching the latest news...")
        news_headlines = get_news(num_articles=5)
        if news_headlines:
            speak(f"Here are the top 5 headlines:")
            for i, article in enumerate(news_headlines, 1):
                print(f"Headline {i}: {article['title']}.")
                print(f"Description: {article['description']}")
        else:
            speak("Sorry, I couldn't fetch the news.")
