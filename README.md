# CycleDash

Inky setup instructions from https://github.com/pimoroni/inky
```sudo raspi-config nonint do_i2c 0```
```sudo raspi-config nonint do_spi 0```

possibly add `dtoverlay=spi0-0cs` to `/boot/firmware/config.txt`

yellow #e7de23

Run the full pipeline, including writing to the display with
```
uv run pipeline.py
```

To just fetch the day and render the html, without taking a snapshot and showing on the display, run
```
uv run pipeline.py -sd
```