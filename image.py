#!/usr/bin/env python3

import pathlib
import typer
from PIL import Image
from inky.auto import auto

app = typer.Typer()

@app.command()
def run(
    file: pathlib.Path = typer.Option(
        ..., 
        "--file",
        "-f",
        help="Path to the image file to display.",
        exists=True,    
        file_okay=True,  
        dir_okay=False,   
        readable=True,    
    ),
    saturation: float = typer.Option(
        0.5,
        "--saturation",
        "-s",
        min=0.0,
        max=1.0,
        help="Colour palette saturation (from 0.0 to 1.0).",
    ),
):
    """
    Resizes and displays an image on the Inky display.
    """
    try:
        inky = auto(ask_user=True, verbose=True)
    except Exception as e:
        typer.echo(f"Error initializing Inky display: {e}")
        raise typer.Exit(code=1)

    typer.echo(f"Display resolution: {inky.resolution[0]}x{inky.resolution[1]}")
    typer.echo(f"Loading image: {file}")

    image = Image.open(file)
    resized_image = image.resize(inky.resolution)

    try:
        inky.set_image(resized_image, saturation=saturation)
    except TypeError:
        typer.echo("Display does not support saturation. Setting image in monochrome.")
        inky.set_image(resized_image)

    typer.echo("Displaying image...")
    inky.show()
    typer.echo("Done!")


if __name__ == "__main__":
    app()