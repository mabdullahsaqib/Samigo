import os

from dotenv import load_dotenv

load_dotenv()

# Firebase configuration
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH")

# Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Google Custom Search API configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# Gmail API configuration
GMAIL_CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH")
GMAIL_TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH")

# News API key
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Weather API configuration
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_API_HOST = os.getenv("WEATHER_API_HOST")