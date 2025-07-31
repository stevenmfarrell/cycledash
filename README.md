# CycleDash

Inky setup instructions from https://github.com/pimoroni/inky
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0

possibly add `dtoverlay=spi0-0cs` to `/boot/firmware/config.txt`