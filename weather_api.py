import pprint
import requests
from models import CycleWeather, AirQualityForecast
import datetime
from typing import List
from settings import settings
from wmo_codes import get_wmo_weather_description


def get_open_meteo_hourly_weather(lat, long) -> List[CycleWeather]:
    open_meteo_fields = [
        "precipitation_probability",
        "temperature",
        "apparent_temperature",
        "wind_gusts_10m",
        "uv_index",
        "weather_code",
        "wind_direction_10m",
        "wind_speed_10m",
    ]
    query_params = {
        "latitude": lat,
        "longitude": long,
        "hourly": {",".join(open_meteo_fields)},
        "timezone": settings.timezone,
        "forecast_days": 1,
        "wind_speed_unit": "mph",
        "temperature_unit": "fahrenheit",
        "precipitation_unit": "inch",
        "forecast_hours": 24,
        "timeformat": "unixtime",
    }
    url = "https://api.open-meteo.com/v1/forecast"
    raw_weather = requests.get(url, params=query_params).json()
    # pprint.pprint(raw_weather)
    weathers = []
    for i in range(24):
        weather = CycleWeather(
            time=datetime.datetime.fromtimestamp(
                raw_weather["hourly"]["time"][i], tz=settings.zoneinfo
            ),
            feels_like_temperature_f=raw_weather["hourly"]["apparent_temperature"][i],
            temperature_f=raw_weather["hourly"]["temperature"][i],
            text=get_wmo_weather_description(
                raw_weather["hourly"]["weather_code"][i], False
            ),
            wind_gust_mph=raw_weather["hourly"]["wind_gusts_10m"][i],
            wind_speed_mph=raw_weather["hourly"]["wind_speed_10m"][i],
            uv_index=raw_weather["hourly"]["uv_index"][i],
            wmo_weather_code=raw_weather["hourly"]["weather_code"][i],
            precipitation_probability=float(
                raw_weather["hourly"]["precipitation_probability"][i] / 100
            ),
            wind_direction_deg=raw_weather["hourly"]["wind_direction_10m"][i],
        )
        weathers.append(weather)

    return weathers

air_quality_map = {
    1: "good",
    2: "fair",
    3: "moderate",
    4: "poor",
    5: "very poor"
}

def get_openweathermap_air_quality(lat, long) -> list[AirQualityForecast]:
    query_params = {
        "lat": lat,
        "lon": long,
        "appid": settings.openweathermap_api_key,
        "units": "imperial",
    }
    url = "https://api.openweathermap.org/data/2.5/air_pollution/forecast"
    response = requests.get(url, params=query_params)
    if response.status_code == 200:
        resp = response.json()
        air_quality_forecasts = []
        for item in resp["list"]:
            air_quality_forecasts.append(
                AirQualityForecast(
                    time=datetime.datetime.fromtimestamp(
                        item["dt"], tz=settings.zoneinfo
                    ),
                    air_quality=air_quality_map[item["main"]["aqi"]],
                )
            )
        return air_quality_forecasts
    else:
        raise Exception(f"Error fetching air quality data: {response.status_code}")


def get_weather_at_times(lat, long, hours: List[int]) -> List[CycleWeather]:
    weathers = get_open_meteo_hourly_weather(lat, long)
    cycle_forecasts: list[CycleWeather] = []
    hours = [8, 17]  # commute times
    for weather in weathers:
        hour = weather.time.hour
        if hour in hours:
            cycle_forecasts.append(weather)
        if len(cycle_forecasts) == len(hours):
            break
    air_quality=get_openweathermap_air_quality(lat, long)
    for forecast in cycle_forecasts:
        for aq in air_quality:
            if aq.time == forecast.time:
                forecast.air_quality = aq.air_quality
    return cycle_forecasts


if __name__ == "__main__":
    lat_lon = (settings.latitude, settings.longitude)
    # cycle_forecasts = get_weather_at_times(lat_lon[0], lat_lon[1], [8, 17])
    aq = get_openweathermap_air_quality(lat_lon[0], lat_lon[1])
    # for forecast in cycle_forecasts:
    #    pprint.pprint(forecast.model_dump_json())
    for aqi in aq:
        pprint.pprint(aqi.model_dump())
