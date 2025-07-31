from cal_api import get_calendar_api_service, get_events_for_calendars
from datetime import date, datetime, timedelta, time
from weather_api import get_weather_at_times
from settings import settings
from models import DataPackage
import pprint
from genai_api import get_genai_weather_summary
def main():
    calendar_service = get_calendar_api_service()
    today = datetime.combine(date.today(), time())
    tomorrow = today + timedelta(days=1)
    after_tomorrow = tomorrow + timedelta(days=1)
    future = after_tomorrow + timedelta(days=7)
    todays_events = get_events_for_calendars(settings.calendar_ids, calendar_service, today, tomorrow)
    tomorrow_events = get_events_for_calendars(settings.calendar_ids, calendar_service, tomorrow, after_tomorrow)
    other_events = get_events_for_calendars(settings.calendar_ids, calendar_service, after_tomorrow, future)
    weathers = get_weather_at_times(settings.latitude, settings.longitude, settings.timezone, [8, 17])

    for weather in weathers:
        pprint.pprint(weather.model_dump())
    summaries = [get_genai_weather_summary(weather) for weather in weathers]

    for summary in summaries:
        pprint.pprint(summary.model_dump())
    print("Today's Events:")
    for e in todays_events:
        print(f"- {e.title} ({e.start_datetime} to {e.end_datetime})")
    print("\nTomorrow's Events:")
    for e in tomorrow_events:
        print(f"- {e.title} ({e.start_datetime} to {e.end_datetime})")
    print("\nOther Upcoming Events:")
    for e in other_events:
        print(f"- {e.title} ({e.start_datetime} to {e.end_datetime})")
    data_package = DataPackage(
        today_events=todays_events,
        tomorrow_events=tomorrow_events,
        future_events=other_events,
        morning_weather=weathers[0],
        afternoon_weather=weathers[1],
        morning_weather_assessment=summaries[0],
        afternoon_weather_assessment=sumaries[1]
    )


if __name__ == "__main__":
    main()
