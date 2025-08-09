import pprint
import requests
from models import CycleWeather
import pytz
import datetime
from typing import List
from settings import settings
from wmo_codes import get_wmo_weather_description
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
            temperature_f=raw_weather['hourly']['temperature'][i],
            text = get_wmo_weather_description(raw_weather['hourly']['weather_code'][i], False),
            wind_gust_mph=raw_weather['hourly']['wind_gusts_10m'][i],
            wind_speed_mph=raw_weather['hourly']['wind_speed_10m'][i],
            uv_index=raw_weather['hourly']['uv_index'][i],
            wmo_weather_code=raw_weather['hourly']['weather_code'][i],
            precipitation_probability=float(raw_weather['hourly']['precipitation_probability'][i]/100),
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
