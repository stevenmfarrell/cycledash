import traceback
from models import CycleWeather, CycleAssessment
from google import genai
from settings import settings
from returns.result import Result, Success, Failure

api_key = settings.google_ai_api_key


def get_genai_weather_summary(
    weather: CycleWeather,
) -> Result[CycleAssessment, Exception]:
    client = genai.Client(api_key=api_key)
    prompt = f"""
    Consider the following weather forecast, as a JSON string:

    {weather.model_dump_json()}
    
    Your task is to decide if it's good weather conditions for cycling or not, and explain why. 
    High temperature is not a problem, but consider especially the chance of precipitation, the wind, and cold, and if the air quality is any worse than "moderate".

    Respond back with the cycling conditions, whether it's good conditions, bad conditions, or maybe.
    Also respond with a short 2-4 word summary describing the weather conditions.
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": CycleAssessment,
            },
        )
        raw_response = response.text

        assessment = CycleAssessment.model_validate_json(raw_response)  # type: ignore
        return Success(assessment)
    except Exception as e:
        traceback.print_exc()
        return Failure(e)
