import requests

from .config import WEATHER_API_KEY, WEATHER_API_HOST, NEWS_API_KEY

# Weather API setup
WEATHER_API_URL = "https://weatherapi-com.p.rapidapi.com/current.json"

# News API setup
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"


# Weather fetching function
def get_weather(location):
    """
    Fetches the current weather for a specified location.

    Parameters:
        location (str): The location for which to fetch the weather.

    Returns:
        dict: A dictionary with weather data or None if an error occurs.
    """
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
        return {"error": str(e)}


# News fetching function
def get_news(country="us", category="general", num_articles=5):
    """
    Fetches the latest news headlines.

    Parameters:
        country (str): The country code for the news (default is 'us').
        category (str): The news category (default is 'general').
        num_articles (int): The number of articles to fetch (default is 5).

    Returns:
        list: A list of news articles or None if an error occurs.
    """
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
        return {"error": str(e)}


# Function to handle voice commands for Weather and News (Refactored for Flask)
def weather_and_news_voice_interaction(data):
    """
    Handles voice commands for fetching weather and news.

    Parameters:
        data (dict): A dictionary containing the user's request. The command can be 'weather' or 'news'.

    Returns:
        dict: A response dictionary with weather or news information, or an error message.
    """
    command = data.get("command", "")
    payload = data.get("payload", {})

    if "weather" in command:
        location = payload.get("location", "Zurich").strip()  # Default location if none provided
        weather_info = get_weather(location)
        if "error" in weather_info:
            response = {"error": "Unable to fetch weather data."}
        else:
            response = weather_info

    elif "news" in command:
        category = payload.get("category", "general").strip()  # Default category if none provided
        news_headlines = get_news(category=category, num_articles=5)
        if "error" in news_headlines:
            response = {"error": "Unable to fetch news data."}
        else:
            response = {"news": news_headlines}

    else:
        response = {"error": "Command not recognized. Please use 'weather' or 'news'."}

    return response
