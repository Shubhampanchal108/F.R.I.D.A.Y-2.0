import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config_driver import Check_Keys

NEWS_API_KEY = Check_Keys("KEYS", "NEWS_API_KEY")

def get_latest_news():
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        return {
            "error": f"Failed to fetch news. Status code: {response.status_code}"
        }

    data = response.json()
    articles = data.get("articles", [])

    if not articles:
        return {
            "news": []
        }

    headlines = []
    for article in articles[:5]:
        if article.get("title"):
            headlines.append(article["title"])

    return {
        "top_headlines": headlines
    }
