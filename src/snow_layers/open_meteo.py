"""Client minimal pour les données historiques publiques Open-Meteo."""

from __future__ import annotations

from collections import defaultdict
from datetime import date

import requests


ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
SOURCE_NAME = "Open-Meteo Archive (ERA5-Land, hauteur de neige modélisée)"


def fetch_daily_snow_depth(
    *, latitude: float, longitude: float, elevation_m: float, start_date: date, end_date: date
) -> tuple[list[tuple[date, float]], str]:
    """Récupère la neige horaire puis enregistre une moyenne journalière en cm.

    Open-Meteo expose la hauteur de neige en mètres et à pas horaire. Une
    moyenne locale des 24 pas est utilisée afin d'obtenir une série quotidienne
    stable et comparable entre saisons.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "elevation": elevation_m,
        "hourly": "snow_depth",
        "models": "era5_land",
        "timezone": "Europe/Paris",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }
    response = requests.get(ARCHIVE_URL, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    hourly = payload["hourly"]
    by_day: dict[date, list[float]] = defaultdict(list)
    for timestamp, depth_m in zip(hourly["time"], hourly["snow_depth"], strict=True):
        if depth_m is not None:
            by_day[date.fromisoformat(timestamp[:10])].append(float(depth_m) * 100)

    daily = [(day, round(sum(values) / len(values), 1)) for day, values in sorted(by_day.items()) if values]
    return daily, response.url
