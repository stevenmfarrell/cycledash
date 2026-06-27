import pprint
import requests
import stamina
from models import AirQuality, AppResult, CycleWeather, AirQualityForecast
import datetime
from settings import settings
from wmo_codes import get_wmo_weather_description
from returns.result import Result, Success, Failure
import traceback


def get_open_meteo_hourly_weather(lat, long) -> Result[list[CycleWeather], Exception]:
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

    @stamina.retry(on=Exception, attempts=3)
    def _fetch():
        response = requests.get(url, params=query_params)
        response.raise_for_status()
        raw_weather = response.json()
        weathers = []
        for i in range(24):
            weather = CycleWeather(
                time=datetime.datetime.fromtimestamp(
                    raw_weather["hourly"]["time"][i], tz=settings.zoneinfo
                ),
                feels_like_temperature_f=raw_weather["hourly"]["apparent_temperature"][
                    i
                ],
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

    try:
        return Success(_fetch())
    except Exception as e:
        traceback.print_exc()
        return Failure(e)


air_quality_map: dict[int, AirQuality] = {
    1: "good",
    2: "fair",
    3: "moderate",
    4: "poor",
    5: "very poor",
}


def get_openweathermap_air_quality(
    lat, long
) -> Result[list[AirQualityForecast], Exception]:
    query_params = {
        "lat": lat,
        "lon": long,
        "appid": settings.openweathermap_api_key,
        "units": "imperial",
    }
    url = "https://api.openweathermap.org/data/2.5/air_pollution/forecast"

    @stamina.retry(on=Exception, attempts=3)
    def _fetch():
        response = requests.get(url, params=query_params)
        response.raise_for_status()
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

    try:
        return Success(_fetch())
    except Exception as e:
        traceback.print_exc()
        return Failure(e)


def _filter_weathers_for_hours(weathers: list[CycleWeather], hours: list[int]):
    filtered: list[CycleWeather] = []
    for weather in weathers:
        hour = weather.time.hour
        if hour in hours:
            filtered.append(weather)
        if len(filtered) == len(hours):
            break
    return filtered


def _join_aq_to_weathers(
    weathers: list[CycleWeather], aqs: list[AirQualityForecast]
) -> list[CycleWeather]:
    for forecast in weathers:
        for aq in aqs:
            if aq.time == forecast.time:
                forecast.air_quality = aq.air_quality
    return weathers


def get_weather_at_times(
    lat, long, hours: list[int]
) -> AppResult[list[CycleWeather], str]:
    weathers_result = get_open_meteo_hourly_weather(lat, long)

    match weathers_result:
        case Failure(e):
            return AppResult(
                data=None, errors=[f"Failed to fetch weather ({type(e).__name__})"]
            )
        case Success(weathers):
            cycle_forecasts = _filter_weathers_for_hours(weathers, hours)
            air_quality_result = get_openweathermap_air_quality(lat, long)
            match air_quality_result:
                case Failure(e):
                    return AppResult(
                        data=cycle_forecasts,
                        errors=[f"Failed to fetch air quality ({type(e).__name__})"],
                    )
                case Success(air_qualities):
                    cycle_forecasts = _join_aq_to_weathers(
                        cycle_forecasts, air_qualities
                    )
                    return AppResult(data=cycle_forecasts)
    return AppResult(data=None, errors=["Unreachable code"])


if __name__ == "__main__":
    lat_lon = (settings.latitude, settings.longitude)
    # cycle_forecasts = get_weather_at_times(lat_lon[0], lat_lon[1], [8, 17])
    aq = get_openweathermap_air_quality(lat_lon[0], lat_lon[1])
    match aq:
        case Success(aq):
            for aqi in aq:
                pprint.pprint(aqi.model_dump())
        case Failure(e):
            print(e)
