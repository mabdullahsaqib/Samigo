
import requests


from src.config import WEATHER_API_KEY, WEATHER_API_HOST, NEWS_API_KEY


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







# Function to handle voice commands for Weather and News
def weather_and_news_voice_interaction(command):
    if "weather" in command:
        weather_info = get_weather("Canada")
        if weather_info:
            print(
                f"The weather in {weather_info['location']} is {weather_info['temperature']} degrees Celsius, {weather_info['condition']}.")
            print(
                f"The humidity is {weather_info['humidity']}%, and the wind speed is {weather_info['wind_speed']} kilometers per hour.")
        else:
            print("Sorry, I couldn't fetch the weather information.")

    elif "news" in command:
        print("Fetching the latest news...")
        news_headlines = get_news(num_articles=5)
        if news_headlines:
            print(f"Here are the top 5 headlines:")
            for i, article in enumerate(news_headlines, 1):
                print(f"Headline {i}: {article['title']}.")
                print(f"Description: {article['description']}")
        else:
            print("Sorry, I couldn't fetch the news.")
