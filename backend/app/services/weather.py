"""
Free Open-Meteo Weather Service for Project SREE
Zero-cost, requires no API key, provides live weather and forecasts.
"""

import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("sree.weather")

class WeatherService:
    def __init__(self):
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.weather_url = "https://api.open-meteo.com/v1/forecast"

    async def get_coordinates(self, city: str) -> Optional[Dict[str, Any]]:
        """Geocode city name to latitude/longitude."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(self.geocoding_url, params={"name": city, "count": 1, "language": "en", "format": "json"})
                if res.status_code == 200:
                    data = res.json()
                    results = data.get("results")
                    if results:
                        return {
                            "name": results[0].get("name"),
                            "country": results[0].get("country"),
                            "lat": results[0].get("latitude"),
                            "lon": results[0].get("longitude")
                        }
        except Exception as e:
            logger.warning(f"Geocoding error for {city}: {e}")
        return None

    async def get_weather(self, city: str = "auto") -> Dict[str, Any]:
        """
        Fetch current weather conditions and daily summary.
        If city is 'auto', defaults to local or geolocated coordinates.
        """
        # Default coordinates (fallback or detect)
        lat, lon, location_name = 13.0827, 80.2707, "Chennai, India" # Default regional coords
        
        if city and city.lower() != "auto":
            coords = await self.get_coordinates(city)
            if coords:
                lat = coords["lat"]
                lon = coords["lon"]
                location_name = f"{coords['name']}, {coords['country']}"

        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                params = {
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
                    "daily": "weather_code,temperature_2m_max,temperature_2m_min",
                    "timezone": "auto"
                }
                res = await client.get(self.weather_url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    curr = data.get("current", {})
                    daily = data.get("daily", {})
                    
                    # Map WMO weather codes to plain text
                    code = curr.get("weather_code", 0)
                    weather_desc = self._wmo_code_to_text(code)

                    return {
                        "success": True,
                        "location": location_name,
                        "temperature_c": curr.get("temperature_2m"),
                        "feels_like_c": curr.get("apparent_temperature"),
                        "humidity_percent": curr.get("relative_humidity_2m"),
                        "wind_speed_kmh": curr.get("wind_speed_10m"),
                        "condition": weather_desc,
                        "temp_max_c": daily.get("temperature_2m_max", [None])[0],
                        "temp_min_c": daily.get("temperature_2m_min", [None])[0]
                    }
        except Exception as e:
            logger.error(f"Weather fetch failed: {e}")

        return {"success": False, "error": "Unable to fetch live weather telemetry."}

    def _wmo_code_to_text(self, code: int) -> str:
        codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            80: "Rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            95: "Thunderstorm"
        }
        return codes.get(code, "Clear")

weather_service = WeatherService()

