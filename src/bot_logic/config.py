import os

from dotenv import load_dotenv

load_dotenv()

# Configurations
PROJECT_ID = os.getenv("PROJECT_ID")
AUTH_URI = os.getenv("AUTH_URI")
TOKEN_URI = os.getenv("TOKEN_URI")

# Firebase configuration
FIREBASE_CREDENTIALS_TYPE = os.getenv("FIREBASE_CREDENTIALS_TYPE")
FIREBASE_PRIVATE_KEY = os.getenv("FIREBASE_PRIVATE_KEY")
FIREBASE_CLIENT_EMAIL = os.getenv("FIREBASE_CLIENT_EMAIL")

# Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Google Custom Search API configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# Gmail API configuration
GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")
GMAIL_AUTH_PROVIDER_CERT = os.getenv("GMAIL_AUTH_PROVIDER_CERT")

GMAIL_TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH")

# News API key
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Weather API configuration
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_API_HOST = os.getenv("WEATHER_API_HOST")
