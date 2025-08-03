from models import DataPackage, CycleWeather, CalendarEvent
import jinja2
from wmo_codes import get_wmo_weather_image
from datetime import datetime

data_package_file = "data_package.json"

def pick_display_temperature(weather: CycleWeather) -> float:
    if weather.feels_like_temperature_f > 50:
        return max(weather.temperature_f, weather.feels_like_temperature_f)
    else:
        return min(weather.temperature_f, weather.feels_like_temperature_f)

def format_time_ampm(dt: datetime) -> str:
    """
    Converts a datetime or timestamp to a string like '7 PM' or '8:30 AM'.
    Accepts a datetime object or a timestamp (seconds since epoch).
    """
    hour = dt.hour
    minute = dt.minute
    ampm = "AM" if hour < 12 else "PM"
    hour12 = hour % 12 or 12
    if minute == 0:
        return f"{hour12} {ampm}"
    else:
        return f"{hour12}:{minute:02d} {ampm}"

def get_detailed_event_string(event: CalendarEvent) -> str:
    """
    Returns a detailed string representation of a calendar event.
    """
    if event.is_all_day:
        return f"{event.title}"
    return f"{event.title} - {format_time_ampm(event.start_datetime)}"

def get_event_string_with_date(event: CalendarEvent) -> str:
    """
    Returns a string representation of a calendar event with the date included.
    """
    date_str = event.start_datetime.strftime("%B %d")
    return f"{event.title} - {date_str}"

def sort_events(events: list[CalendarEvent]) -> list[CalendarEvent]:
    """
    Sorts CalendarEvents: all-day events first, then by start_datetime.
    """
    return sorted(
        events,
        key=lambda e: (not e.is_all_day, e.start_datetime)
    )
with open(data_package_file, "r") as f:
    data_package = DataPackage.model_validate_json(f.read())

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(searchpath="./"),
    autoescape=jinja2.select_autoescape(["html", "xml"]),
)
template = env.get_template("dashboard_template.jinja")

placeholder_image = "https://placehold.co/100x100/FFFFFF/000000?text=SUN"

today_events = sort_events(data_package.today_events)
tomorrow_events = sort_events(data_package.tomorrow_events)
future_events = [get_event_string_with_date(event) for event in data_package.future_events]
if len(today_events) + len(tomorrow_events) + len(future_events) > 6:
    future_length = min(6 - len(today_events) - len(tomorrow_events), 0)
    future_events = future_events[:6 - len(today_events) - len(tomorrow_events)]

# Render the template with the data package
rendered_html = template.render(
    date_title=data_package.morning_weather.time.strftime("%A, %B %d"),
    morning_image_url=get_wmo_weather_image(data_package.morning_weather.wmo_weather_code,True),
    afternoon_image_url=get_wmo_weather_image(data_package.afternoon_weather.wmo_weather_code, True),
    morning_temperature=int(pick_display_temperature(data_package.morning_weather)),
    afternoon_temperature=int(pick_display_temperature(data_package.afternoon_weather)),
    morning_forecast=data_package.morning_weather.text,
    afternoon_forecast=data_package.afternoon_weather.text,
    today_events=[get_detailed_event_string(event) for event in today_events],
    tomorrow_events=[get_detailed_event_string(event) for event in tomorrow_events],
    future_events=[get_event_string_with_date(event) for event in future_events],
    morning_time=format_time_ampm(data_package.morning_weather.time),
    afternoon_time=format_time_ampm(data_package.afternoon_weather.time),
    morning_conditions=data_package.morning_weather_assessment.conditions,
    afternoon_conditions=data_package.afternoon_weather_assessment.conditions,
    morning_reason=data_package.morning_weather_assessment.reason,
    afternoon_reason=data_package.afternoon_weather_assessment.reason,
)
output_file = "dashboard.html"
with open(output_file, "w") as f:
    f.write(rendered_html)
