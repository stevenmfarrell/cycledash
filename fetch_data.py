from pathlib import Path
from cal_api import get_calendar_api_service, get_events_for_calendars
from datetime import date, datetime, timedelta, time
from weather_api import get_weather_at_times
from settings import settings
from models import CycleAssessment, DataPackage
from sun_api import get_sunrise_sunset
from genai_api import get_genai_weather_summary
from returns.result import Success, Failure


def run(data_package_file: Path = settings.data_package_file):
    errors: list[str] = []
    today_date = date.today()
    calendar_service = get_calendar_api_service()
    today = datetime.combine(today_date, time())
    cutoff = today + timedelta(days=settings.lookahead_days)
    events_result = get_events_for_calendars(
        settings.calendar_ids, calendar_service, today, cutoff, max_per_cal=8
    )
    errors.extend(events_result.errors)
    commute_hours = [settings.morning_commute_hour, settings.afternoon_commute_hour]

    weathers_result = get_weather_at_times(
        settings.latitude, settings.longitude, commute_hours
    )
    errors.extend(weathers_result.errors)

    morning_weather = None
    afternoon_weather = None
    if weathers_result.data is not None:
        for weather in weathers_result.data:
            if weather.time.hour == settings.morning_commute_hour:
                morning_weather = weather
            elif weather.time.hour == settings.afternoon_commute_hour:
                afternoon_weather = weather

    morning_assessment = None
    if morning_weather is not None:
        summaries_result = get_genai_weather_summary(morning_weather)
        match summaries_result:
            case Success(assessment):
                morning_assessment = assessment
            case Failure(e):
                morning_assessment = CycleAssessment(conditions="maybe", summary=morning_weather.text)
                errors.append(f"Failed to fetch AI morning weather summary ({type(e).__name__})")
    else:
        morning_assessment = CycleAssessment(conditions="bad", summary="No data")

    afternoon_assessment = None
    if afternoon_weather is not None:
        summaries_result = get_genai_weather_summary(afternoon_weather)
        match summaries_result:
            case Success(assessment):
                afternoon_assessment = assessment
            case Failure(e):
                afternoon_assessment = CycleAssessment(conditions="maybe", summary=afternoon_weather.text)
                errors.append(f"Failed to fetch AI afternoon weather summary ({type(e).__name__})")
    else:
        afternoon_assessment = CycleAssessment(conditions="bad", summary="No data")

    sun_times_today = get_sunrise_sunset(
        today_date, settings.timezone, settings.latitude, settings.longitude
    )
    sun_times_tomorrow = get_sunrise_sunset(
        today_date + timedelta(days=1),
        settings.timezone,
        settings.latitude,
        settings.longitude,
    )

    data_package = DataPackage(
        date=today_date,
        today_sunrise=sun_times_today[0].astimezone(settings.zoneinfo),
        today_sunset=sun_times_today[1].astimezone(settings.zoneinfo),
        tomorrow_sunrise=sun_times_tomorrow[0].astimezone(settings.zoneinfo),
        tomorrow_sunset=sun_times_tomorrow[1].astimezone(settings.zoneinfo),
        events=events_result.data or [],
        morning_weather=morning_weather,
        afternoon_weather=afternoon_weather,
        morning_weather_assessment=morning_assessment,
        afternoon_weather_assessment=afternoon_assessment,
        errors=errors
    )
    with open(data_package_file, "w") as f:
        f.write(data_package.model_dump_json(indent=2))
        print(f"Data package saved to {data_package_file}")


if __name__ == "__main__":
    run()
