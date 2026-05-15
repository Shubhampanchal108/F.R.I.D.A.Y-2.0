import pywhatkit

def play_youtube(query: str):
    try:
        pywhatkit.playonyt(query)

        return {
            "status": "success",
            "query": query
        }

    except Exception as e:
        return {"error": str(e)}
