from pydantic_settings import BaseSettings
from pydantic import computed_field
from zoneinfo import ZoneInfo
class ProjectSettings(BaseSettings):
    """
    Settings for the calendar API.
    """
    google_calendar_service_account_file: str = "service_account.json"
    google_calendar_scopes: list[str] = ["https://www.googleapis.com/auth/calendar.readonly"]
    google_ai_api_key: str = ""
    calendar_ids: list[str] = []
    morning_commute_hour: int = 8
    afternoon_commute_hour: int = 17
    lookahead_days: int = 10
    timezone: str = "America/Denver"
    @computed_field
    @property
    def zoneinfo(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)
    latitude: float = 0.0
    longitude: float = 0.0
    image_file: str = "dash.png"
    data_package_file: str = "data_package.json"
    dashboard_template_file: str = "dashboard_template.jinja"
    dashboard_html_file: str = "dashboard.html"
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = ProjectSettings()