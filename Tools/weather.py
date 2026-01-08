import requests

WEATHER_KEY = "2888314fe95f78d2be18da5a6099af04"


def get_current_weather(city: str):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_KEY}"
    res = requests.get(url).json()

    if res.get("cod") != 200:
        return {"error": "City not found"}

    return {
        "city": city,
        "weather": res["weather"][0]["main"],
        "temperature_c": round(res["main"]["temp"] - 273.15, 2),
        "feels_like_c": round(res["main"]["feels_like"] - 273.15, 2)
    }
