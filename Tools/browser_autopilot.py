import requests
import re
import sys
from bs4 import BeautifulSoup

# UTF-8 stdout reconfigure for Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def extract_webpage_content(url: str, max_chars: int = 3500):
    """
    Scrapes and extracts main readable text content from any web page.
    Useful for reading articles, technical docs, blogs, or web pages.
    """
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=12)
        if response.status_code != 200:
            return {"status": "error", "message": f"HTTP Error {response.status_code}"}

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style tags
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()

        title = soup.title.string.strip() if soup.title and soup.title.string else url

        # Extract text content
        text = soup.get_text(separator="\n")
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = "\n".join(chunk for chunk in chunks if chunk)

        if len(clean_text) > max_chars:
            clean_text = clean_text[:max_chars] + "\n... [Content Truncated]"

        return {
            "status": "success",
            "title": title,
            "url": url,
            "content": clean_text
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    print("🌐 Testing Browser Autopilot...")
    res = extract_webpage_content("https://python.org")
    print("Title:", res.get("title"))
    print("Snippet:", res.get("content")[:200])
