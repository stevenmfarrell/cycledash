from pydantic_settings import BaseSettings

class ProjectSettings(BaseSettings):
    """
    Settings for the calendar API.
    """
    google_calendar_service_account_file: str = "service_account.json"
    google_calendar_scopes: list[str] = ["https://www.googleapis.com/auth/calendar.readonly"]
    google_ai_api_key: str = ""
    calendar_ids: list[str] = []
    timezone: str = "America/Denver"
    latitude: float = 0.0
    longitude: float = 0.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = ProjectSettings()