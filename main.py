import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(".env")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def set_light_values(brightness: str, color_temp: str):
    """Set the brightness and color temperature of a room light. (mock API).

    Args:
        brightness: Light level from 0 to 100. Zero is off and 100 is full brightness
        color_temp: Color temperature of the light fixture, which can be `daylight`, `cool` or `warm`.

    Returns:
        A dictionary containing the set brightness and color temperature.
    """
    return {
        "brightness": brightness,
        "colorTemperature": color_temp
    }


model = genai.GenerativeModel(
    model_name="gemini-1.5-pro-002",
    tools=[set_light_values],
)

chat = model.start_chat()
response = chat.send_message('Dim the lights so the room feels cozy and warm.')
for part in response.parts:
    if fn := part.function_call:
        args = ", ".join(f"{key}={val}" for key, val in fn.args.items())
        print(f"{fn.name}({args})")

