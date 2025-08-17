from typing import Literal, Optional
from pydantic import BaseModel
from datetime import date, datetime
from dataclasses import dataclass, field
class CalendarEvent(BaseModel):
    title: str
    start_datetime: datetime
    end_datetime: datetime
    is_all_day: bool = False

AirQuality = Literal['good', 'fair', 'moderate', 'poor', 'very poor']

class CycleWeather(BaseModel):
    time: datetime
    temperature_f: float
    feels_like_temperature_f: float
    uv_index: Optional[float] = None
    precipitation_probability: float
    text: str
    wind_gust_mph: Optional[float] = None
    wind_speed_mph: float
    air_quality: Optional[AirQuality]= None
    wmo_weather_code: int
    wind_direction_deg: float

class AirQualityForecast(BaseModel):
    time: datetime
    air_quality: Optional[AirQuality] = None

CycleConditions = Literal['good', 'bad', 'maybe']

class CycleAssessment(BaseModel):
    conditions: CycleConditions
    summary: str


@dataclass
class AppResult[T, S]:
    """
    A generic container that holds a potential successful result of type 'T'
    and a list of any errors that occurred during the operation.
    """
    data: T | None
    errors: list[S] = field(default_factory=list)

    def has_errors(self) -> bool:
        return bool(self.errors)

class DataPackage(BaseModel):
    date: date
    today_sunrise: datetime
    today_sunset: datetime
    tomorrow_sunrise: datetime
    tomorrow_sunset: datetime
    events: list[CalendarEvent]
    morning_weather: CycleWeather | None
    afternoon_weather: CycleWeather | None
    morning_weather_assessment: CycleAssessment
    afternoon_weather_assessment: CycleAssessment
    errors: list[str]
