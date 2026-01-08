import requests

NEWS_API_KEY = "996ab15c58294d689db44016488f38a9"

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
