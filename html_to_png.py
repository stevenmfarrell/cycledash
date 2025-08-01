import subprocess
from PIL import Image
import os
import typer
from typing_extensions import Annotated

# --- Typer App Initialization ---
app = typer.Typer(
    help="A tool to capture a webpage screenshot using Chromium and crop it to a specific size."
)

# --- Configuration Constants ---
TEMP_SCREENSHOT_NAME = "temp_screenshot.png"
CAPTURE_WIDTH = 800
CAPTURE_HEIGHT = 600  # Larger height to capture everything plus the blue bar
FINAL_WIDTH = 800
FINAL_HEIGHT = 480

# --- Main Script Logic as a CLI Command ---

@app.command()
def run(
    html_file: Annotated[str, typer.Argument(
        help="The path to the input HTML file to capture."
    )],
    output_file: Annotated[str, typer.Argument(
        help="The path for the final, cropped output image."
    )] = "dash.png",
):
    """
    Executes the Chromium command to take a screenshot and then crops the result.
    """
    # 1. Check if the input file exists before doing anything.
    if not os.path.exists(html_file):
        print(f"Error: The input file '{html_file}' was not found.")
        raise typer.Exit(code=1)

    # 2. Construct the shell command to take the screenshot.
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

    print("Step 1: Taking screenshot with Chromium...")
    try:
        # Execute the command. check=True will raise an error if the command fails.
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Successfully created temporary screenshot: {TEMP_SCREENSHOT_NAME}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing Chromium command: {e}")
        print(f"Stderr: {e.stderr}")
        raise typer.Exit(code=1)
    except FileNotFoundError:
        print("Error: 'chromium-browser' command not found.")
        print("Please ensure Chromium is installed and in your system's PATH.")
        raise typer.Exit(code=1)

    # 3. Crop the resulting image.
    print(f"\nStep 2: Cropping the image to {FINAL_WIDTH}x{FINAL_HEIGHT}...")
    try:
        with Image.open(TEMP_SCREENSHOT_NAME) as img:
            # Define the crop box (left, upper, right, lower).
            crop_box = (0, 0, FINAL_WIDTH, FINAL_HEIGHT)
            
            cropped_img = img.crop(crop_box)
            cropped_img.save(output_file)
            print(f"Successfully cropped image and saved as: {output_file}")

    except FileNotFoundError:
        print(f"Error: Could not find the temporary screenshot '{TEMP_SCREENSHOT_NAME}'.")
        raise typer.Exit(code=1)
    except Exception as e:
        print(f"An error occurred during cropping: {e}")
        raise typer.Exit(code=1)
    finally:
        # 4. Clean up the temporary screenshot file.
        if os.path.exists(TEMP_SCREENSHOT_NAME):
            os.remove(TEMP_SCREENSHOT_NAME)
            print(f"\nStep 3: Cleaned up temporary file.")


if __name__ == "__main__":
    app()
