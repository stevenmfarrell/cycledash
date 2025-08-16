from typing import Literal, Optional
from pydantic import BaseModel
from datetime import date, datetime

class CalendarEvent(BaseModel):
    title: str
    start_datetime: datetime
    end_datetime: datetime
    is_all_day: bool = False

AirQuality = Literal['good', 'fair', 'moderate', 'poor', 'very poor']

class CycleWeather(BaseModel):
    time: datetime
    temperature_f: Optional[float] = None
    feels_like_temperature_f: Optional[float] = None
    uv_index: Optional[float] = None
    precipitation_probability: Optional[float] = None
    text: Optional[str] = None
    wind_gust_mph: Optional[float] = None
    wind_speed_mph: Optional[float] = None
    air_quality: Optional[AirQuality]= None
    wmo_weather_code: Optional[int] = None
    wind_direction_deg: Optional[float] = None

class AirQualityForecast(BaseModel):
    time: datetime
    air_quality: Optional[AirQuality] = None

CycleConditions = Literal['good', 'bad', 'maybe']

class CycleAssessment(BaseModel):
    conditions: CycleConditions
    summary: str

class DataPackage(BaseModel):
    date: date
    today_sunrise: datetime
    today_sunset: datetime
    tomorrow_sunrise: datetime
    tomorrow_sunset: datetime
    events: list[CalendarEvent]
    morning_weather: CycleWeather
    afternoon_weather: CycleWeather
    morning_weather_assessment: CycleAssessment
    afternoon_weather_assessment: CycleAssessment
