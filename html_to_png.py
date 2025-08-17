import subprocess
from PIL import Image
from pathlib import Path
import os
import typer
from typing_extensions import Annotated
from settings import settings
app = typer.Typer(
    help="A tool to capture a webpage screenshot using Chromium and crop it to a specific size."
)

TEMP_SCREENSHOT_NAME = "temp_screenshot.png"
CAPTURE_WIDTH = 480
CAPTURE_HEIGHT = 1000
FINAL_WIDTH = 480
FINAL_HEIGHT = 800


@app.command()
def run(
    html_file: Annotated[Path, typer.Argument(
        help="The path to the input HTML file to capture."
    )],
    output_file: Annotated[Path, typer.Argument(
        help="The path for the final, cropped output image."
    )] = settings.image_file,
):
    """
    Executes the Chromium command to take a screenshot and then crops the result.
    """
    if not os.path.exists(html_file):
        print(f"Error: The input file '{html_file}' was not found.")
        raise typer.Exit(code=1)

    command = [
        "chromium-browser",
        html_file,
        "--headless",
        f"--screenshot={TEMP_SCREENSHOT_NAME}",
        f'--window-size={CAPTURE_WIDTH},{CAPTURE_HEIGHT}',
        "--disable-gpu",
        "--no-sandbox",
        "--virtual-time-budget=5000"
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing Chromium command: {e}")
        print(f"Stderr: {e.stderr}")
        raise typer.Exit(code=1)
    except FileNotFoundError:
        print("Error: 'chromium-browser' command not found.")
        print("Please ensure Chromium is installed and in your system's PATH.")
        raise typer.Exit(code=1)
    try:
        with Image.open(TEMP_SCREENSHOT_NAME) as img:
            crop_box = (0, 0, FINAL_WIDTH, FINAL_HEIGHT)
            cropped_img = img.crop(crop_box)
            cropped_img = cropped_img.transpose(Image.Transpose.ROTATE_90)
            cropped_img.save(output_file)
            print(f"Successfully took snapshot and saved as: {output_file}")

    except FileNotFoundError:
        print(f"Error: Could not find the temporary screenshot '{TEMP_SCREENSHOT_NAME}'.")
        raise typer.Exit(code=1)
    except Exception as e:
        print(f"An error occurred during cropping: {e}")
        raise typer.Exit(code=1)
    finally:
        if os.path.exists(TEMP_SCREENSHOT_NAME):
            os.remove(TEMP_SCREENSHOT_NAME)

if __name__ == "__main__":
    app()
