from vo.Models import WeatherReport
import requests
import logging

logger = logging.getLogger(__name__)

class WeatherService():
    def get_weather_object(self, city_name: str) -> WeatherReport:
        """
        Retrieves weather data for a given city using the Open-Meteo API.

        Args:
            city_name (str): The name of the city.

        Returns:
            WeatherReport: A Pydantic model containing the weather report, or None if the city is not found.
        """
        try:
            # 1. Geocode the city name to get latitude and longitude.
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&format=json"
            geo_res_json = requests.get(geo_url).json()
            if "results" not in geo_res_json:
                return None
            geo_res = geo_res_json["results"][0]
            
            # 2. Get the current weather using the latitude and longitude.
            lat, lon = geo_res["latitude"], geo_res["longitude"]
            w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m"
            w_res = requests.get(w_url).json()["current"]
            
            # 3. Instantiate and return the WeatherReport model with the retrieved data.
            return WeatherReport(
                city=geo_res["name"],
                country=geo_res["country"],
                **w_res # Unpacks temperature_2m and relative_humidity_2m directly
            )
        except (requests.exceptions.RequestException, KeyError, IndexError) as e:
            logger.error(f"An error occurred while getting weather for {city_name}: {e}", exc_info=True)
            return None
