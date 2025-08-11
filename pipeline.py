from typing_extensions import Annotated
from fetch_data import run as generate_data_package
from generate_dashboard import run as generate_dashboard
from html_to_png import run as capture_screenshot
import typer
from pathlib import Path

app = typer.Typer()


@app.command()
def main(
    data_package_file: Annotated[
        Path, typer.Option(help="Path to the data package JSON file.")
    ] = Path("data_package.json"),
    html_file: Annotated[
        Path, typer.Option(help="Path for the output HTML dashboard.")
    ] = Path("dashboard.html"),
    template_file: Annotated[
        Path, typer.Option(help="Path to the dashboard's Jinja template.")
    ] = Path("dashboard_template.jinja"),
    image_file: Annotated[
        Path, typer.Option(help="Path for the output PNG screenshot.")
    ] = Path("dash.png"),
    saturation: Annotated[
        float,
        typer.Option(min=0.0, max=1.0, help="Saturation level for the final image."),
    ] = 0.5,
    skip_data_fetch: Annotated[
        bool,
        typer.Option(
            "--skip-data-fetch",
            help="Skip the data generation step and use existing data.",
            is_flag=True,
        ),
    ] = False,
    skip_display: Annotated[
        bool,
        typer.Option(
            "--skip-display",
            help="Do not display the image on the Inky display.",
            is_flag=True,
        ),
    ] = False,
    skip_screenshot: Annotated[
        bool,
        typer.Option(
            "--skip-screenshot",
            help="Do not capture a screenshot of the HTML dashboard.",
            is_flag=True,
        ),
    ] = False,
):
    """
    A CLI to generate a data dashboard and capture a screenshot.
    """
    print("--- Starting Dashboard Generation Process ---")
    if not skip_data_fetch:
        generate_data_package(data_package_file)
        print("📦 Data package generated and saved to:", data_package_file)
    else:
        print("⏭️  Skipping data generation and reusing existing data package.")
    generate_dashboard(data_package_file, html_file, template_file)
    print("📄 Dashboard generated and saved to:", html_file)
    if not skip_screenshot:
        capture_screenshot(html_file, image_file)
        print("📸 Screenshot captured and saved to:", image_file)
    else:
        print("⏭️  Skipping screenshot capture.")
    if not skip_display:
        from image import run as display_image
        display_image(file=image_file, saturation=saturation)
        print("🖼️  Displayed image on Inky display")
    else:
        print("⏭️  Skipping image display on Inky")


if __name__ == "__main__":
    app()
