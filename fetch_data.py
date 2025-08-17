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

    assessments: list[CycleAssessment] = []
    if weathers_result.data is not None:
        for weather in weathers_result.data:
            summaries_result = get_genai_weather_summary(weather)
            match summaries_result:
                case Success(assessment):
                    assessments.append(assessment)
                case Failure(e):
                    assessment = CycleAssessment(
                        conditions="maybe", summary=weather.text
                    )
                    errors.append(f"Failed to fetch AI weather summary ({type(e).__name__})")
    else:
        assessments = [
            CycleAssessment(conditions="bad", summary="No data"),
            CycleAssessment(conditions="bad", summary="No data"),
        ]

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
        morning_weather=weathers_result.data[0] if weathers_result.data else None,
        afternoon_weather=weathers_result.data[1] if weathers_result.data else None,
        morning_weather_assessment=assessments[0],
        afternoon_weather_assessment=assessments[1],
        errors=errors
    )
    with open(data_package_file, "w") as f:
        f.write(data_package.model_dump_json(indent=2))
        print(f"Data package saved to {data_package_file}")


if __name__ == "__main__":
    run()
