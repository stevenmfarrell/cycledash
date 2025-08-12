import datetime as dt
from models import CalendarEvent
from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import datetime, timedelta
from settings import settings

def get_calendar_api_service():
    """Authenticates using a service account key file."""
    creds = service_account.Credentials.from_service_account_file(
        settings.google_calendar_service_account_file, scopes=settings.google_calendar_scopes
    )
    service = build("calendar", "v3", credentials=creds)
    return service


def parse_event_to_calendar_event(event: dict) -> CalendarEvent:
    """Parses a Google Calendar event dictionary to a CalendarEvent model."""
    if "dateTime" in event["start"]:
        e = CalendarEvent.model_validate(
            {
                "title": event["summary"],
                "start_datetime": event["start"].get("dateTime"),
                "end_datetime": event["end"].get("dateTime"),
                "is_all_day": False,
            }
        )
    else:
        e = CalendarEvent.model_validate(
            {
                "title": event["summary"],
                "start_datetime": datetime.strptime(event["start"].get("date"), "%Y-%m-%d").astimezone(settings.zoneinfo),
                "end_datetime": datetime.strptime(event["end"].get("date"), "%Y-%m-%d").astimezone(settings.zoneinfo),
                "is_all_day": True,
            }
        )
    return e


def get_events_for_calendar(
    calendar_id: str,
    service,
    start_time: dt.datetime,
    end_time: dt.datetime,
    max_results: int = 6,
) -> list[dict]:
    start = start_time.astimezone(dt.UTC).isoformat()
    end = end_time.astimezone(dt.UTC).isoformat()

    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=start,
            timeMax=end,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])
    cal_events: list[CalendarEvent] = [parse_event_to_calendar_event(e) for e in events]
    return cal_events


def get_events_for_calendars(calendars: list[str], service, start_time: dt.datetime, end_time: dt.datetime, max_per_cal: int = 6) -> list[CalendarEvent]:
    service = get_calendar_api_service()
    all_events: list[CalendarEvent] = []
    for calendar_id in calendars:
        events = get_events_for_calendar(
            calendar_id, service, start_time, end_time)
        all_events.extend(events)
    all_events = sorted(all_events, key=lambda e: e.start_datetime)
    return all_events


if __name__ == "__main__":
    service = get_calendar_api_service()
    events = get_events_for_calendars(settings.calendar_ids, service, datetime.now(), datetime.now() + timedelta(days=7))
    for e in events:
        print(e)
