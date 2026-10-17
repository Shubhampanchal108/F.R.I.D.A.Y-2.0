def play_youtube(query: str):
    try:
        import pywhatkit
        pywhatkit.playonyt(query)
        return {
            "status": "success",
            "query": query
        }
    except Exception as e:
        # Fallback using webbrowser in case pywhatkit fails
        try:
            import urllib.parse
            import webbrowser
            encoded_query = urllib.parse.quote_plus(query)
            webbrowser.open(f"https://www.youtube.com/results?search_query={encoded_query}")
            return {
                "status": "success",
                "query": query,
                "note": "Opened YouTube search in browser"
            }
        except Exception as fallback_err:
            return {"error": f"{str(e)} | fallback: {str(fallback_err)}"}
