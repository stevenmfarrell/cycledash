from models import (
    CycleAssessment,
    CycleConditions,
    DataPackage,
    CycleWeather,
    CalendarEvent,
)
import jinja2
from wmo_codes import get_wmo_weather_image
from datetime import datetime, time, date, timedelta
import pytz
from settings import settings

data_package_file = "data_package.json"
tz = pytz.timezone(settings.timezone)


def pick_display_temperature(weather: CycleWeather) -> float:
    if weather.feels_like_temperature_f > 50:
        return max(weather.temperature_f, weather.feels_like_temperature_f)
    else:
        return min(weather.temperature_f, weather.feels_like_temperature_f)


def get_wind_rotation(degrees):
    rotation = (round(degrees / 15) * 15 + 90) % 360
    return int(rotation)


def get_wind_text(weather: CycleWeather) -> str:
    return f"{round(weather.wind_speed_mph)}"


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


def get_today_event_tuple(event: CalendarEvent) -> tuple[str, str]:
    if event.is_all_day:
        return ("All Day", event.title)
    return (format_time_ampm(event.start_datetime), event.title)


def get_tomorrow_event_tuple(event: CalendarEvent) -> tuple[str, str]:
    if event.is_all_day:
        return ("Tomorrow", f"{event.title}")
    return ("Tomorrow", f"{event.title} - {format_time_ampm(event.start_datetime)}")


def get_future_event_tuple(event: CalendarEvent) -> tuple[str, str]:
    if event.is_all_day:
        return (event.start_datetime.strftime("%b %-d"), f"{event.title}")
    return (
        event.start_datetime.strftime("%b %-d"),
        f"{event.title} - {format_time_ampm(event.start_datetime)}",
    )


def sort_events(events: list[CalendarEvent]) -> list[CalendarEvent]:
    """
    Sorts CalendarEvents: all-day events first, then by start_datetime.
    """
    return sorted(
        events,
        key=lambda e: e.start_datetime
        if not e.is_all_day
        else datetime.combine(e.start_datetime, time.min, tzinfo=tz),
    )


def combine_conditions(c1: CycleConditions, c2: CycleConditions) -> CycleConditions:
    if c1 == "bad" or c2 == "bad":
        return "bad"
    if c1 == "maybe" or c2 == "maybe":
        return "maybe"
    return "good"


def get_forecast_svg(weather: CycleWeather) -> str:
    """
    Better to inline the svg so we can apply syles
    """
    image_path = get_wmo_weather_image(weather.wmo_weather_code, True)
    with open(image_path, "r") as f:
        svg_content = f.read()
    modified_svg = svg_content.replace("<svg ", '<svg class="weather-icon" ', 1)

    return modified_svg


with open(data_package_file, "r") as f:
    data_package = DataPackage.model_validate_json(f.read())


env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(searchpath="./"),
    autoescape=jinja2.select_autoescape(["html", "xml"]),
)
template = env.get_template("dashboard_template.jinja")

today_events = sort_events(data_package.today_events)
today_event_tuples = [get_today_event_tuple(event) for event in today_events]
tomorrow_events = sort_events(data_package.tomorrow_events)
future_events = sort_events(data_package.future_events)
other_event_tuples = [get_tomorrow_event_tuple(event) for event in tomorrow_events] + [
    get_future_event_tuple(event) for event in future_events
]
other_event_tuples = other_event_tuples[: 10 - int(1.5 * len(today_event_tuples))]


def get_display_forecast_data(
    date_context: date, weather: CycleWeather, assessment: CycleAssessment
):
    time_str = format_time_ampm(weather.time)
    if weather.time.date() == date_context + timedelta(days=1):
        time_str = f"{time_str} TOMORROW"
    forecast = {
        "temperature": round(pick_display_temperature(weather)),
        "summary": assessment.summary,
        "conditions": assessment.conditions,
        "wind_speed": round(weather.wind_speed_mph),
        "wind_rotation": get_wind_rotation(weather.wind_direction_deg),
        "precip": f"{round(weather.precipitation_probability * 100)}%",
        "time": time_str,
        "svg": get_forecast_svg(weather),
    }
    return forecast


display_forecasts = [
    get_display_forecast_data(
        data_package.date,
        data_package.morning_weather,
        data_package.morning_weather_assessment,
    ),
    get_display_forecast_data(
        data_package.date,
        data_package.afternoon_weather,
        data_package.afternoon_weather_assessment,
    ),
]

rendered_html = template.render(
    date_title=data_package.date.strftime("%A, %b %-d"),
    today_events=today_event_tuples,
    future_events=other_event_tuples,
    forecasts=display_forecasts,
    overall_conditions=combine_conditions(
        data_package.morning_weather_assessment.conditions,
        data_package.afternoon_weather_assessment.conditions,
    ),
)
output_file = "dashboard.html"
with open(output_file, "w") as f:
    f.write(rendered_html)
