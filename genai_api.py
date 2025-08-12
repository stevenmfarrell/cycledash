from models import CycleWeather, CycleAssessment
from google import genai
from google.genai import types

from io import BytesIO
from PIL import Image
from settings import settings

api_key = settings.google_ai_api_key


def get_genai_weather_summary(weather: CycleWeather) -> CycleAssessment:
    client = genai.Client(api_key=api_key)
    prompt = f"""
    Consider the following weather forecast, as a JSON string:

    {weather.model_dump_json()}
    
    Your task is to decide if it's good weather conditions for cycling or not, and explain why. High temperature is not a problem, but consider especially the chance of precipitation, the wind, and cold.

    Respond back with the cycling conditions, whether it's good conditions, bad conditions, or maybe.
    Also respond with a short 2-4 word summary describing the weather conditions.
    """
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=prompt,
        config={
            'response_mime_type': 'application/json',
            'response_schema': CycleAssessment,
        }
    )
    raw_response = response.text
    assessment = CycleAssessment.model_validate_json(raw_response)
    return assessment

def get_image(prompt_text: str):
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.0-flash-exp-image-generation",
        contents=(prompt_text),
        config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE']
        )
    )

    for part in response.candidates[0].content.parts:
        if part.text is not None:
            print(part.text)
        elif part.inline_data is not None:
            image = Image.open(BytesIO((part.inline_data.data)))
            image.save('gemini-native-image.png')

if __name__=="__main__":
    prompt = "Generate an image of a cyclist riding in the rain. The image background is uncluttered, and clearly depicts the weather. The art style is playful, flat, and simple, like vector art, or a Google doodle"
    get_image(prompt)
