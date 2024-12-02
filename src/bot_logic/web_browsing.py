import google.generativeai as genai
import requests

from .config import GOOGLE_API_KEY, GOOGLE_CSE_ID, GEMINI_API_KEY

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
            return {"error": "No results found."}

        search_results = [
            {
                "title": item["title"],
                "link": item["link"],
                "snippet": item.get("snippet", "No description available.")
            }
            for item in results["items"]
        ]
        return {"results": search_results}
    except requests.exceptions.RequestException as e:
        return {"error": f"An error occurred while performing the search: {str(e)}"}


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


def web_browsing_voice_interaction(data):
    """
    Web browsing interaction logic for the API.

    Parameters:
        query (str): The search query.
        action (str): Specify action: 'search', 'summarize', or 'open'.
        selected_index (int): Index of the link to open (used for 'open' action).

    Returns:
        dict: Response dictionary containing search results, summary, or a success message for opening links.
    """

    payload = data.get("payload", {})
    query = payload.get("query", "")
    action = payload.get("action", "")

    if not query:
        return {"error": "Query is required for web browsing."}

    results = search_web(query)
    if "error" in results:
        return results

    if action == "summarize":
        summary = summarize_results_with_gemini(results["results"])
        return {"summary": summary}

    # Default action is to return the search results
    return results
