import wikipedia

def search_wikipedia(query: str):
    try:
        summary = wikipedia.summary(query, sentences=2)
        return {
            "query": query,
            "summary": summary
        }

    except wikipedia.exceptions.DisambiguationError as e:
        return {
            "query": query,
            "error": "Multiple results found",
            "options": e.options[:5]
        }

    except wikipedia.exceptions.PageError:
        return {
            "query": query,
            "error": "No page found on Wikipedia"
        }

    except Exception as e:
        return {
            "query": query,
            "error": str(e)
        }

