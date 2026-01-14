import webbrowser
from urllib.parse import urlparse
import time


def open_website(url: str) -> dict:
    start_time = time.time()

    try:
        # --------- URL NORMALIZATION ----------
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        parsed = urlparse(url)
        if not parsed.netloc:
            return {
                "success": False,
                "tool": "web_browser",
                "url": url,
                "error": "Invalid URL format"
            }

        # --------- OPEN IN BROWSER ----------
        opened = webbrowser.open(url, new=2)

        if not opened:
            return {
                "success": False,
                "tool": "web_browser",
                "url": url,
                "error": "Browser failed to open the website"
            }

        load_time = round(time.time() - start_time, 2)

        return {
            "success": True,
            "tool": "web_browser",
            "url": url,
            "message": "Website opened successfully in browser",
            "load_time_sec": load_time
        }

    except Exception as e:
        return {
            "success": False,
            "tool": "web_browser",
            "url": url,
            "error": f"Unexpected error: {str(e)}"
        }
