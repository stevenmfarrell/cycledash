import pprint
import requests
from models import CycleWeather
import pytz
import datetime
from typing import List
from settings import settings
wmo_weather_codes = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm: Heavy",
    99: "Thunderstorm with hail",
}

def get_open_meteo_hourly_weather(lat, long, tz_str) -> List[CycleWeather]:
    tz = pytz.timezone(tz_str)

    open_meteo_fields = ["precipitation_probability", "temperature", "apparent_temperature",
                       "wind_gusts_10m", "uv_index", "weather_code", "wind_direction_10m", "wind_speed_10m"
    ]
    query_params = {
        "latitude": lat,
        "longitude": long,
        "hourly": {','.join(open_meteo_fields)},
        "timezone": tz_str,
        "forecast_days": 1,
        "wind_speed_unit": "mph",
        "temperature_unit": "fahrenheit",
        "precipitation_unit": "inch",
        "forecast_hours": 24,
        "timeformat": "unixtime"
    }
    url = "https://api.open-meteo.com/v1/forecast"
    raw_weather = requests.get(url, params=query_params).json()
    # pprint.pprint(raw_weather)
    weathers = []
    for i in range(24):
        weather = CycleWeather(
            time=datetime.datetime.fromtimestamp(raw_weather['hourly']['time'][i], tz=tz),
            feels_like_temperature_f=raw_weather['hourly']['apparent_temperature'][i],
            temperature_f=raw_weather['hourly']['temperature'][i],  # Assuming apparent temperature is used as the temperature
            text = wmo_weather_codes.get(raw_weather['hourly']['weather_code'][i], None),
            wind_gust_mph=raw_weather['hourly']['wind_gusts_10m'][i],
            wind_speed_mph=raw_weather['hourly']['wind_speed_10m'][i],
            uv_index=raw_weather['hourly']['uv_index'][i],
            precipitation_pct=raw_weather['hourly']['precipitation_probability'][i],
            wind_direction_deg=raw_weather['hourly']['wind_direction_10m'][i],
        )
        weathers.append(weather)

    return weathers

def get_weather_at_times(lat, long, tz_str, hours: List[int]) -> List[CycleWeather]:
    weathers = get_open_meteo_hourly_weather(lat, long, tz_str)
    cycle_forecasts = []
    hours = [8, 17] # commute times
    for weather in weathers:
        hour = weather.time.hour
        if hour in hours:
            cycle_forecasts.append(weather)
        if len(cycle_forecasts)==len(hours):
            break
    return cycle_forecasts

if __name__ == "__main__":
    lat_lon = (settings.latitude, settings.longitude)
    tz_str = settings.timezone
    cycle_forecasts = get_weather_at_times(lat_lon[0], lat_lon[1], tz_str, [8, 17])
    for forecast in cycle_forecasts:
        pprint.pprint(forecast.model_dump_json())
