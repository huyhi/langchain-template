import httpx
from langchain_core.tools import tool

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

_TIMEOUT = httpx.Timeout(30.0)

WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


def _geocode(city: str) -> tuple[float, float, str]:
    """Resolve a city name to (latitude, longitude, display_name)."""
    resp = httpx.get(GEOCODING_URL, params={"name": city, "count": 1, "language": "en", "format": "json"}, timeout=_TIMEOUT)
    resp.raise_for_status()
    results = resp.json().get("results")
    if not results:
        raise ValueError(f"Location '{city}' not found.")
    r = results[0]
    display = f"{r['name']}, {r.get('admin1', '')}, {r.get('country', '')}".strip(", ")
    return r["latitude"], r["longitude"], display


# @tool
def get_current_weather(city: str) -> str:
    """Get the current weather conditions for a given city.

    Args:
        city: The name of the city to get weather for (e.g. 'Singapore', 'London', 'New York').
    """
    lat, lon, display = _geocode(city)
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "weather_code",
            "wind_speed_10m",
            "wind_direction_10m",
            "precipitation",
        ],
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "timezone": "auto",
    }
    resp = httpx.get(WEATHER_URL, params=params, timeout=_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    current = data["current"]
    condition = WMO_CODES.get(current.get("weather_code", -1), "Unknown")

    return (
        f"Current weather in {display}:\n"
        f"  Condition     : {condition}\n"
        f"  Temperature   : {current['temperature_2m']}°C (feels like {current['apparent_temperature']}°C)\n"
        f"  Humidity      : {current['relative_humidity_2m']}%\n"
        f"  Precipitation : {current['precipitation']} mm\n"
        f"  Wind          : {current['wind_speed_10m']} km/h at {current['wind_direction_10m']}°\n"
        f"  Time          : {current['time']} ({data.get('timezone', 'UTC')})"
    )


# @tool
def get_weather_forecast(city: str, days: int = 7) -> str:
    """Get a multi-day weather forecast for a given city.

    Args:
        city: The name of the city to get the forecast for.
        days: Number of forecast days (1-16). Defaults to 7.
    """
    days = max(1, min(days, 16))
    lat, lon, display = _geocode(city)
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max",
        ],
        "forecast_days": days,
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "timezone": "auto",
    }
    resp = httpx.get(WEATHER_URL, params=params, timeout=_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    daily = data["daily"]

    lines = [f"{days}-day forecast for {display}:\n"]
    for i, date in enumerate(daily["time"]):
        condition = WMO_CODES.get(daily["weather_code"][i], "Unknown")
        lines.append(
            f"  {date}  {condition:<30}"
            f"  High: {daily['temperature_2m_max'][i]}°C  "
            f"Low: {daily['temperature_2m_min'][i]}°C  "
            f"Rain: {daily['precipitation_sum'][i]} mm  "
            f"Wind: {daily['wind_speed_10m_max'][i]} km/h"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    print(get_current_weather("Singapore"))
    print(get_weather_forecast("Singapore", 7))
