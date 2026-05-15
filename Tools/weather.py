import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config_driver import Check_Keys

WEATHER_KEY = Check_Keys("KEYS", "WEATHER_KEY")

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
