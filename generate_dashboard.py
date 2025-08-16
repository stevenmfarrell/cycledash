from pathlib import Path
from typing_extensions import Annotated
from models import (
    CycleAssessment,
    CycleConditions,
    DataPackage,
    CycleWeather,
    CalendarEvent,
    AirQuality
)
import jinja2
from sun_api import is_daytime
from wmo_codes import get_wmo_weather_image
from datetime import datetime, time, date, timedelta
from settings import settings
import typer


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
    Converts a datetime or timestamp to a string like '7p' or '8:30a'.
    Accepts a datetime object or a timestamp (seconds since epoch).
    """
    hour = dt.hour
    minute = dt.minute
    ampm = "a" if hour < 12 else "p"
    hour12 = hour % 12 or 12
    if minute == 0:
        return f"{hour12}{ampm}"
    else:
        return f"{hour12}:{minute:02d}{ampm}"


def get_detailed_event_string(event: CalendarEvent) -> str:
    """
    Returns a detailed string representation of a calendar event.
    """
    if event.is_all_day:
        return f"{event.title}"
    return f"{event.title} - {format_time_ampm(event.start_datetime)}"

def get_event_class(event: CalendarEvent) -> str:
    """
    Returns a CSS class for the event based on its type.
    """
    if "birthday" in event.title.lower():
        return "text-gray-600"
    else:
        return ""

def get_display_event(event: CalendarEvent, date_context: date) -> dict[str, str]:
    return {
        "title": event.title,
        "is_today": event.start_datetime.date() == date_context,
        "is_tomorrow": event.start_datetime.date() == date_context + timedelta(days=1),
        "is_all_day": event.is_all_day,
        "date": event.start_datetime.strftime("%b %-d"),
        "day": get_abbreviated_day_of_week(event.start_datetime.date()),
        "start_time": format_time_ampm(event.start_datetime),
        "class": get_event_class(event),
    }

def get_abbreviated_day_of_week(date_obj: date) -> str:
    """
    Returns the abbreviated day of the week for a given datetime.
    """
    CUSTOM_DAY_ABBREVIATIONS = ["M", "Tu", "W", "Th", "F", "Sa", "Su"]
    return CUSTOM_DAY_ABBREVIATIONS[date_obj.weekday()]

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
    daytime = is_daytime(
        weather.time, settings.timezone, settings.latitude, settings.longitude
    )
    image_path = get_wmo_weather_image(weather.wmo_weather_code, daytime)
    with open(image_path, "r") as f:
        svg_content = f.read()
    modified_svg = svg_content.replace("<svg ", '<svg class="weather-icon" ', 1)

    return modified_svg

def get_air_quality_svg(aq: AirQuality) -> str:
    with open('icons/aq_indicator.svg', "r") as f:
        svg_content = f.read()
    mapping = {
        "good": "position-1",
        "fair": "position-2",
        "moderate": "position-3",
        "poor": "position-4",
        "very poor": "position-5",
    }
    modified_svg = svg_content.replace('class="position-1"', f'class="{mapping[aq]}"', 1)

    return modified_svg

def get_sun_svg_path(dt: datetime) -> str:
    """
    Returns the SVG for the sun icon based on whether it's daytime or nighttime.
    """
    if dt.time() < time(12, 0):
        image_path = 'icons/sunrise.svg'
    else:
        image_path = 'icons/sunset.svg'
    return image_path

def get_sun_event_time(date_context: date, dt: datetime, data_package: DataPackage) -> str:
    if dt.date() == date_context and dt.time() < time(12, 0):
        sun_time = data_package.today_sunrise.strftime("%-I:%M %p")
    elif dt.date() == date_context + timedelta(days=1) and dt.time() < time(12, 0):
        sun_time = data_package.tomorrow_sunrise
    elif dt.date() == date_context and dt.time() >= time(12, 0):
        sun_time = data_package.today_sunset
    else:
        sun_time = data_package.tomorrow_sunset
    return sun_time.strftime("%-I:%M")

def get_display_forecast_data(
    date_context: date, weather: CycleWeather, assessment: CycleAssessment, data_package: DataPackage
):
    time_str = format_time_ampm(weather.time)
    if weather.time.date() == date_context + timedelta(days=1):
        time_str = f"{time_str.upper()}M TOMORROW"
    else:
        time_str = f"{time_str.upper()}M"
    forecast = {
        "temperature": round(pick_display_temperature(weather)),
        "summary": assessment.summary,
        "conditions": assessment.conditions,
        "wind_speed": round(weather.wind_speed_mph),
        "wind_rotation": get_wind_rotation(weather.wind_direction_deg),
        "precip": f"{round(weather.precipitation_probability * 100)}%",
        "time": time_str,
        "svg": get_forecast_svg(weather),
        "sun_svg_path": get_sun_svg_path(weather.time),
        "sun_time": get_sun_event_time(date_context, weather.time, data_package),
        "aq_svg": get_air_quality_svg(weather.air_quality)
    }
    return forecast

app = typer.Typer(
    help="A CLI tool to generate an HTML dashboard from a data package JSON file.",
    add_completion=False,
)
@app.command()
def run(
    data_package_file: Annotated[Path, typer.Option(
        "--input",
        "-i",
        help="Path to the input data_package.json file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
    )] = settings.data_package_file,
    output_file: Annotated[Path, typer.Option(
        "--output",
        "-o",
        help="Path for the output html file.",
        writable=True,
        resolve_path=True,
    )] = settings.dashboard_html_file,
    template_file: Annotated[Path, typer.Option(
        "--template",
        "-t",
        help="Path to the Jinja2 template file.",
        exists=True,
        file_okay=True,
        readable=True,
        resolve_path=True,
    )] = settings.dashboard_template_file,
):
    with open(data_package_file, "r") as f:
        data_package = DataPackage.model_validate_json(f.read())


    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(searchpath=template_file.parent),
        autoescape=jinja2.select_autoescape(["html", "xml"]),
    )
    template = env.get_template(template_file.name)
    source_events = data_package.events
    events = [get_display_event(event, data_package.date) for event in source_events]
    today_events = [e for e in events if e["is_today"]]
    other_events = [e for e in events if not e["is_today"]]
    other_events = other_events[: max(8 - round(1.5 * max(len(today_events)-1, 0)), 0)]


    display_forecasts = [
        get_display_forecast_data(
            data_package.date,
            data_package.morning_weather,
            data_package.morning_weather_assessment,
            data_package
        ),
        get_display_forecast_data(
            data_package.date,
            data_package.afternoon_weather,
            data_package.afternoon_weather_assessment,
            data_package
        ),
    ]

    rendered_html = template.render(
        date_title=data_package.date.strftime("%A, %b %-d"),
        today_events=today_events,
        other_events=other_events,
        forecasts=display_forecasts,
        overall_conditions=combine_conditions(
            data_package.morning_weather_assessment.conditions,
            data_package.afternoon_weather_assessment.conditions,
        ),
    )
    with open(output_file, "w") as f:
        f.write(rendered_html)
        print(f"Dashboard HTML generated and saved to {output_file}")

if __name__ == "__main__":
    app()
