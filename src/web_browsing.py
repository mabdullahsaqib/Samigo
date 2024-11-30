import webbrowser

import google.generativeai as genai
import pyttsx3
import requests
import speech_recognition as sr

from config import GOOGLE_API_KEY, GOOGLE_CSE_ID, GEMINI_API_KEY

# Initialize recognizer and text-to-speech
recognizer = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty('rate', 250)  # Adjust speaking rate if needed

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


def search_web(query, num_results=5):
    """
    Perform a web search using Google Custom Search API.

    Parameters:
        query (str): The search query.
        num_results (int): Number of results to return (default is 5).

    Returns:
        list: A list of dictionaries containing titles, links, and snippets of search results.
    """
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "num": num_results
    }

    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()  # Raise an error for unsuccessful status codes
        results = response.json()

        if "items" not in results:
            print("No results found.")
            return []

        search_results = []
        for item in results["items"]:
            search_results.append({
                "title": item["title"],
                "link": item["link"],
                "snippet": item.get("snippet", "No description available.")
            })

        return search_results
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while performing the search: {e}")
        return []


def display_results(results):
    """
    Displays search results in a readable format.

    Parameters:
        results (list): List of search results.
    """
    print("\nSearch Results:")
    for i, result in enumerate(results, start=1):
        print(f"\nResult {i}:")
        print(f"Title: {result['title']}")
        print(f"Link: {result['link']}")
        print(f"Snippet: {result['snippet']}\n")


def summarize_results_with_gemini(results):
    """
    Summarizes the snippets from search results using Gemini API.

    Parameters:
        results (list): List of search results.

    Returns:
        str: Summarized text of search result snippets.
    """
    snippets = " ".join([result["snippet"] for result in results])

    if snippets:
        # Send the snippets to Gemini for summarization
        response = model.generate_content("Summarize the following text: " + snippets)
        return response.text
    return "No content available for summarization."


def open_link(results):
    """
    Allows the user to choose and open a link from the search results.

    Parameters:
        results (list): List of search results.
    """
    for i, result in enumerate(results, start=1):
        print(f"{i}. {result['title']} - {result['link']}")
    speak("Please select a link by saying the corresponding number.")
    choice = listen()
    if choice.isdigit() and 1 <= int(choice) <= len(results):
        webbrowser.open(results[int(choice) - 1]["link"])
        print(f"Opening link: {results[int(choice) - 1]['link']}")
    else:
        print("No link selected.")


def speak(text):
    """Convert text to speech."""
    engine.say(text)
    engine.runAndWait()


def listen():
    """Capture audio input from user."""
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        speak("I didn't catch that.")
        return ""
    except sr.RequestError:
        speak("Voice service unavailable.")
        return ""


def web_browsing_voice_interaction(query):
    """
    Voice interaction for the Web Browsing Module.
    Handles search, displays results, summarizes, and opens links based on voice commands.
    """

    if query:
        # Fetch search results
        speak(f"Searching for {query}.")
        results = search_web(query)

        # Display results
        speak("Here are the top search results.")
        display_results(results)

        # Summarize results with Gemini
        speak("Would you like a summary of the results?")
        if "yes" in listen().lower():
            summary = summarize_results_with_gemini(results)
            speak("Here is a summary of the search results.")
            print("\nSummary of Search Results:\n", summary)

        # Open a link if requested
        speak("Would you like to open any of these links?")
        response = listen().lower()
        if "yes" in response:
            open_link(results)
        else:
            speak("Returning to search query mode. Please provide another query or say 'exit' to quit.")
