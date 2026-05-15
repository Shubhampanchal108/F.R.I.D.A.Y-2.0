import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config_driver import Check_Keys

TAVILY_API_KEY = Check_Keys("KEYS", "TAVILY_API_KEY")


def google_search(query: str, max_results: int = 2):
    url = "https://api.tavily.com/search"

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "include_answer": True,
        "include_raw_content": False,
        "max_results": max_results
    }

    try:
        response = requests.post(url, json=payload)
        data = response.json()

        if response.status_code != 200:
            return {"error": data.get("error", "Search failed")}

        results = []

        for item in data.get("results", []):
            results.append({
                "title": item.get("title"),
                "url": item.get("url"),
                "content": item.get("content")
            })

        return {
            "query": query,
            "answer": data.get("answer"),
            "results": results
        }

    except Exception as e:
        return {"error": str(e)}
    


def summrize_url(url: str):
    endpoint = "https://api.tavily.com/extract"

    payload = {
        "api_key": TAVILY_API_KEY,
        "urls": [url],
        "include_images": False,
        "extract_depth": "advanced"
    }

    try:
        response = requests.post(endpoint, json=payload)
        data = response.json()

        if response.status_code != 200:
            return {"error": data.get("error", "Extraction failed")}

        results = data.get("results", [])

        if not results:
            return {"error": "No content extracted"}

        extracted = results[0]

        return {
            "url": extracted.get("url"),
            "title": extracted.get("title"),
            "content": extracted.get("content")
        }

    except Exception as e:
        return {"error": str(e)}