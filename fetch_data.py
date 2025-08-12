from cal_api import get_calendar_api_service, get_events_for_calendars
from datetime import date, datetime, timedelta, time
from weather_api import get_weather_at_times
from settings import settings
from models import DataPackage
from sun_api import get_sunrise_sunset
from genai_api import get_genai_weather_summary

def run(data_package_file: str = settings.data_package_file):
    today_date = date.today()
    calendar_service = get_calendar_api_service()
    today = datetime.combine(today_date, time())
    cutoff = today + timedelta(days=21)
    events = get_events_for_calendars(settings.calendar_ids, calendar_service, today, cutoff, max_per_cal=8)
    commute_hours = [settings.morning_commute_hour, settings.afternoon_commute_hour]
    weathers = get_weather_at_times(settings.latitude, settings.longitude, commute_hours)

    sun_times = get_sunrise_sunset(today_date, settings.timezone, settings.latitude, settings.longitude)

    summaries = [get_genai_weather_summary(weather) for weather in weathers]

    data_package = DataPackage(
        date=today_date,
        sunrise=sun_times[0].astimezone(settings.zoneinfo),
        sunset=sun_times[1].astimezone(settings.zoneinfo),
        events=events,
        morning_weather=weathers[0],
        afternoon_weather=weathers[1],
        morning_weather_assessment=summaries[0],
        afternoon_weather_assessment=summaries[1]
    )
    with open(data_package_file, "w") as f:
        f.write(data_package.model_dump_json(indent=2))
        print(f"Data package saved to {data_package_file}")


if __name__ == "__main__":
    run()
