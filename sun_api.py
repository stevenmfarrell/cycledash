from astral import LocationInfo
from astral.sun import sun
from datetime import date, datetime

def get_sunrise_sunset(date_obj: date, tz_str: str, lat: float, long: float) -> tuple[datetime, datetime]:
    location = LocationInfo("My Location", "Custom", tz_str, lat, long)
    sun_times = sun(location.observer, date=date_obj, tzinfo=location.timezone)
    return (sun_times['sunrise'], sun_times['sunset'])

def is_daytime(datetime_obj: datetime, tz_str: str, lat: float, long: float) -> bool:
    date_obj = datetime_obj.date()
    sunrise, sunset = get_sunrise_sunset(date_obj, tz_str, lat, long)
    return sunrise <= datetime_obj <= sunset
