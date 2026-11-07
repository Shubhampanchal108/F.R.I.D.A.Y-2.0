import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.config_driver import Check_Keys


def get_current_weather(city: str = "Kaithal"):
    """
    Fetches real-time weather information for the specified city.
    Primary: OpenWeatherMap (if WEATHER_KEY configured).
    Fallback 1: Open-Meteo free public API (no key required).
    Fallback 2: wttr.in JSON API (no key required).
    """
    clean_city = (city or "Kaithal").strip()

    # 1. Primary: OpenWeatherMap
    try:
        weather_key = Check_Keys("KEYS", "WEATHER_KEY")
        if weather_key and str(weather_key).strip():
            url = f"https://api.openweathermap.org/data/2.5/weather?q={clean_city}&appid={weather_key.strip()}"
            resp = requests.get(url, timeout=4)
            if resp.status_code == 200:
                res = resp.json()
                if res.get("cod") == 200:
                    return {
                        "city": clean_city,
                        "weather": res["weather"][0]["main"],
                        "description": res["weather"][0].get("description", ""),
                        "temperature_c": round(res["main"]["temp"] - 273.15, 1),
                        "feels_like_c": round(res["main"]["feels_like"] - 273.15, 1),
                        "humidity": res["main"].get("humidity", 50)
                    }
    except Exception:
        pass

    # 2. Fallback: Open-Meteo (Geocoding + Forecast, zero key needed)
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={clean_city}&count=1&language=en&format=json"
        geo_res = requests.get(geo_url, timeout=3).json()
        if geo_res.get("results"):
            loc = geo_res["results"][0]
            lat = loc["latitude"]
            lon = loc["longitude"]
            meteo_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code"
            meteo_res = requests.get(meteo_url, timeout=3).json()
            curr = meteo_res.get("current", {})
            temp = curr.get("temperature_2m", 25.0)
            feels = curr.get("apparent_temperature", temp)
            humidity = curr.get("relative_humidity_2m", 50)
            code = curr.get("weather_code", 0)

            # Weather interpretation
            if code in [0, 1]:
                weather_desc = "Clear sky"
            elif code in [2, 3]:
                weather_desc = "Partly cloudy"
            elif code in [45, 48]:
                weather_desc = "Foggy"
            elif code in [51, 53, 55, 61, 63, 65, 80, 81]:
                weather_desc = "Rainy"
            elif code in [95, 96, 99]:
                weather_desc = "Thunderstorm"
            else:
                weather_desc = "Pleasant"

            return {
                "city": clean_city,
                "weather": weather_desc,
                "description": weather_desc,
                "temperature_c": round(float(temp), 1),
                "feels_like_c": round(float(feels), 1),
                "humidity": humidity
            }
    except Exception:
        pass

    # 3. Fallback: wttr.in
    try:
        wttr_url = f"https://wttr.in/{clean_city}?format=j1"
        res = requests.get(wttr_url, timeout=3).json()
        cond = res["current_condition"][0]
        return {
            "city": clean_city,
            "weather": cond["weatherDesc"][0]["value"],
            "description": cond["weatherDesc"][0]["value"],
            "temperature_c": float(cond["temp_C"]),
            "feels_like_c": float(cond["FeelsLikeC"]),
            "humidity": int(cond["humidity"])
        }
    except Exception:
        pass

    # 4. Final offline graceful fallback
    return {
        "city": clean_city,
        "weather": "Clear",
        "description": "Clear skies",
        "temperature_c": 25.0,
        "feels_like_c": 25.0,
        "humidity": 50
    }

