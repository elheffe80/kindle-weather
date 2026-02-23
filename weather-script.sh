#!/bin/sh
set -eu

cd "$(dirname "$0")"

python3 weather-script.py
rsvg-convert --background-color=white -o weather-script-output.png weather-script-output.svg
pngcrush -c 0 -ow weather-script-output.png
install -m 0644 weather-script-output.png /var/www/html/weather-script-output.png
