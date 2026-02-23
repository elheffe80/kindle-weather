#!/usr/bin/env python3

"""Generate SVG weather output for the Kindle weather display.

Security hardening:
- Use HTTPS for NWS data fetches.
- Enforce network timeouts to avoid hanging forever.
- Use secure XML parsing protections from stdlib Expat.
- Sanitize remote icon tokens before injecting into SVG output.
- Fail fast with explicit errors when required weather fields are missing.
"""

from __future__ import annotations

import datetime
import pathlib
import re
import urllib.parse
import urllib.request
import xml.dom.expatbuilder

BASE_DIR = pathlib.Path(__file__).resolve().parent
INPUT_TEMPLATE = BASE_DIR / "weather-script-preprocess.svg"
OUTPUT_SVG = BASE_DIR / "weather-script-output.svg"

NWS_ENDPOINT = "https://graphical.weather.gov/xml/SOAP_server/ndfdSOAPclientByDay.php"
REQUEST_TIMEOUT_SECONDS = 15
NUM_DAYS = 4

ICON_TOKEN_RE = re.compile(r"^[a-z0-9_-]+$")


def fetch_weather_xml() -> bytes:
    """Download weather XML from NWS over HTTPS with a bounded timeout."""
    params = {
        "whichClient": "NDFDgenByDay",
        "lat": "38.7197",
        "lon": "-77.1546",
        "format": "24 hourly",
        "numDays": str(NUM_DAYS),
        "Unit": "e",
    }
    query = urllib.parse.urlencode(params)
    url = f"{NWS_ENDPOINT}?{query}"
    with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return response.read()


def parse_weather(weather_xml: bytes) -> tuple[list[int], list[int], list[str], datetime.datetime]:
    """Parse required weather fields from the returned XML document."""
    # Disable external entities for defense in depth when parsing untrusted XML.
    parser = xml.dom.expatbuilder.DefusedExpatBuilderNS()
    dom = parser.parseString(weather_xml)

    highs: list[int | None] = [None] * NUM_DAYS
    lows: list[int | None] = [None] * NUM_DAYS

    for item in dom.getElementsByTagName("temperature"):
        values = item.getElementsByTagName("value")
        if item.getAttribute("type") == "maximum":
            for i in range(min(NUM_DAYS, len(values))):
                if values[i].firstChild is not None:
                    highs[i] = int(values[i].firstChild.nodeValue)
        if item.getAttribute("type") == "minimum":
            for i in range(min(NUM_DAYS, len(values))):
                if values[i].firstChild is not None:
                    lows[i] = int(values[i].firstChild.nodeValue)

    xml_icons = dom.getElementsByTagName("icon-link")
    icons: list[str] = []
    for i in range(NUM_DAYS):
        token = "na"
        if i < len(xml_icons) and xml_icons[i].firstChild is not None:
            raw = xml_icons[i].firstChild.nodeValue.split("/")[-1].split(".")[0].rstrip("0123456789")
            normalized = raw.lower()
            if ICON_TOKEN_RE.fullmatch(normalized):
                token = normalized
        icons.append(token)

    xml_start_times = dom.getElementsByTagName("start-valid-time")
    if not xml_start_times or xml_start_times[0].firstChild is None:
        raise ValueError("Weather feed did not contain start-valid-time")

    xml_day_one = xml_start_times[0].firstChild.nodeValue[0:10]
    day_one = datetime.datetime.strptime(xml_day_one, "%Y-%m-%d")

    if any(v is None for v in highs) or any(v is None for v in lows):
        raise ValueError("Weather feed did not contain complete high/low temperature data")

    return highs, lows, icons, day_one


def render_svg(highs: list[int], lows: list[int], icons: list[str], day_one: datetime.datetime) -> str:
    """Populate the SVG template with weather values."""
    output = INPUT_TEMPLATE.read_text(encoding="utf-8")

    output = (
        output.replace("ICON_ONE", icons[0])
        .replace("ICON_TWO", icons[1])
        .replace("ICON_THREE", icons[2])
        .replace("ICON_FOUR", icons[3])
    )
    output = (
        output.replace("HIGH_ONE", str(highs[0]))
        .replace("HIGH_TWO", str(highs[1]))
        .replace("HIGH_THREE", str(highs[2]))
        .replace("HIGH_FOUR", str(highs[3]))
    )
    output = (
        output.replace("LOW_ONE", str(lows[0]))
        .replace("LOW_TWO", str(lows[1]))
        .replace("LOW_THREE", str(lows[2]))
        .replace("LOW_FOUR", str(lows[3]))
    )

    one_day = datetime.timedelta(days=1)
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Caturday", "Sunday"]
    output = output.replace("DAY_THREE", days_of_week[(day_one + 2 * one_day).weekday()]).replace(
        "DAY_FOUR", days_of_week[(day_one + 3 * one_day).weekday()]
    )

    return output


def main() -> None:
    weather_xml = fetch_weather_xml()
    highs, lows, icons, day_one = parse_weather(weather_xml)
    output = render_svg(highs, lows, icons, day_one)
    OUTPUT_SVG.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    main()
