import pywhatkit
import webbrowser
import time
import pyautogui

def play_youtube(query: str):
    try:
        pywhatkit.playonyt(query)

        return {
            "status": "success",
            "query": query
        }

    except Exception as e:
        return {"error": str(e)}



def google_search(query: str):
    try:
        pywhatkit.search(query)

        return {
            "status": "success",
            "query": query
        }

    except Exception as e:
        return {"error": str(e)}
