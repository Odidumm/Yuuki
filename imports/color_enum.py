import json
import re
from pathlib import Path

CONFIG_PATH = Path("config.json")


def get_color(color_enum: str) -> int:
    """
    Gibt den Dezimalwert einer Farbe aus der config.json zurück
    Nutzung: get_color("success")
    """

    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        config = json.load(file)

    try:
        rgb_string = config["colors"][color_enum]
    except KeyError:
        raise KeyError(f"Color-Enum '{color_enum}' existiert nicht in der Config")

    match = re.match(
        r"rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)",
        rgb_string
    )

    if not match:
        raise ValueError(f"Ungültiges RGB-Format: {rgb_string}")

    r, g, b = map(int, match.groups())

    if not all(0 <= v <= 255 for v in (r, g, b)):
        raise ValueError("RGB-Werte müssen zwischen 0 und 255 liegen")

    return (r << 16) + (g << 8) + b