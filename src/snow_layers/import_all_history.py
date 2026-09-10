"""Importe l'historique ERA5-Land de toutes les stations du catalogue.

Une requête couvre toute la période pour une station. La réponse brute est
conservée dans data/raw afin de permettre une reprise sans nouvel appel API.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import date
from pathlib import Path

import requests

from snow_layers.database import create_session_factory
from snow_layers.open_meteo import ARCHIVE_URL, SOURCE_NAME
from snow_layers.repository import get_or_create_station, upsert_observations
from snow_layers.stations import STATIONS, STATIONS_BY_SLUG


FIRST_SEASON = 1950
CACHE_DIR = Path("data/raw/open_meteo_archive")


def _cache_path(slug: str, start: date, end: date) -> Path:
    return CACHE_DIR / f"{slug}_{start.isoformat()}_{end.isoformat()}.json"


def _daily_from_payload(payload: dict):
    from collections import defaultdict
    from datetime import date as date_type

    by_day = defaultdict(list)
    for timestamp, depth_m in zip(payload["hourly"]["time"], payload["hourly"]["snow_depth"], strict=True):
        if depth_m is not None:
            by_day[date_type.fromisoformat(timestamp[:10])].append(float(depth_m) * 100)
    return [(day, round(sum(values) / len(values), 1)) for day, values in sorted(by_day.items()) if values]


def fetch_cached_daily(*, station: dict, start: date, end: date, refresh: bool = False):
    """Récupère une station, en passant par le cache JSON local quand possible."""
    cache_path = _cache_path(station["slug"], start, end)
    if cache_path.exists() and not refresh:
        payload = json.loads(cache_path.read_text())
        return _daily_from_payload(payload), payload.get("source_url", "cache://open-meteo")

    params = {
        "latitude": station["latitude"], "longitude": station["longitude"],
        "elevation": station["elevation_m"], "hourly": "snow_depth",
        "models": "era5_land", "timezone": "Europe/Paris",
        "start_date": start.isoformat(), "end_date": end.isoformat(),
    }
    response = requests.get(ARCHIVE_URL, params=params, timeout=120)
    response.raise_for_status()
    payload = response.json()
    payload["source_url"] = response.url
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(payload))
    # Reuse the production conversion code after writing the response.
    return fetch_cached_daily(station=station, start=start, end=end)


def fetch_batch(stations: list[dict], *, start: date, end: date) -> dict[str, tuple[list, str]]:
    """Télécharge plusieurs coordonnées dans une seule réponse Open-Meteo."""
    params = {
        "latitude": ",".join(str(item["latitude"]) for item in stations),
        "longitude": ",".join(str(item["longitude"]) for item in stations),
        "elevation": ",".join(str(item["elevation_m"]) for item in stations),
        "hourly": "snow_depth", "models": "era5_land", "timezone": "Europe/Paris",
        "start_date": start.isoformat(), "end_date": end.isoformat(),
    }
    response = None
    for attempt in range(5):
        response = requests.get(ARCHIVE_URL, params=params, timeout=240)
        if response.status_code != 429:
            break
        wait_seconds = 30 * (attempt + 1)
        print(f"    Limite Open-Meteo atteinte ; nouvelle tentative dans {wait_seconds} s", flush=True)
        time.sleep(wait_seconds)
    response.raise_for_status()
    payloads = response.json()
    if isinstance(payloads, dict) and len(stations) == 1:
        payloads = [payloads]
    if not isinstance(payloads, list) or len(payloads) != len(stations):
        raise ValueError("Réponse multi-stations Open-Meteo inattendue")
    result = {}
    for station, payload in zip(stations, payloads, strict=True):
        payload["source_url"] = response.url
        path = _cache_path(station["slug"], start, end)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload))
        result[station["slug"]] = (_daily_from_payload(payload), response.url)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Importe toutes les saisons depuis 1950 pour les stations du catalogue.")
    parser.add_argument("--from-year", type=int, default=FIRST_SEASON, help="Premier hiver, par défaut 1950-1951.")
    parser.add_argument("--to-year", type=int, default=date.today().year - 1, help="Dernier hiver terminé.")
    parser.add_argument("--station", choices=sorted(STATIONS_BY_SLUG), help="Limiter à une station.")
    parser.add_argument("--refresh", action="store_true", help="Ignorer le cache JSON et refaire les appels.")
    parser.add_argument("--batch-size", type=int, default=4, help="Nombre de stations par requête, par défaut 4.")
    parser.add_argument("--chunk-years", type=int, default=10, help="Taille des tranches historiques, par défaut 10 ans.")
    args = parser.parse_args()
    if args.from_year < FIRST_SEASON or args.to_year < args.from_year:
        parser.error("La période doit commencer en 1950 et rester croissante.")

    start, end = date(args.from_year, 12, 1), date(args.to_year + 1, 4, 30)
    stations = [STATIONS_BY_SLUG[args.station]] if args.station else STATIONS
    session_factory = create_session_factory()
    batch_size = max(1, args.batch_size)
    chunk_years = max(1, args.chunk_years)
    for chunk_start in range(args.from_year, args.to_year + 1, chunk_years):
        chunk_end = min(chunk_start + chunk_years - 1, args.to_year)
        chunk_first, chunk_last = date(chunk_start, 12, 1), date(chunk_end + 1, 4, 30)
        for batch_start in range(0, len(stations), batch_size):
            batch = stations[batch_start:batch_start + batch_size]
            pending = [item for item in batch if args.refresh or not _cache_path(item["slug"], chunk_first, chunk_last).exists()]
            downloaded = {}
            if pending:
                try:
                    print(f"[{chunk_start}-{chunk_end}] lot {batch_start + 1}-{batch_start + len(batch)}/{len(stations)} : {len(pending)} station(s)", flush=True)
                    downloaded = fetch_batch(pending, start=chunk_first, end=chunk_last)
                except (requests.RequestException, KeyError, ValueError, TypeError, json.JSONDecodeError) as error:
                    print(f"    ÉCHEC du lot : {error}", flush=True)
            for station in batch:
                try:
                    records, source_url = downloaded.get(station["slug"]) or fetch_cached_daily(station=station, start=chunk_first, end=chunk_last, refresh=False)
                    with session_factory.begin() as session:
                        db_station = get_or_create_station(session, station)
                        count = upsert_observations(session, station=db_station, records=records, source=SOURCE_NAME, source_url=source_url)
                    print(f"    {station['name']} : {count} jours", flush=True)
                except (requests.RequestException, KeyError, ValueError, TypeError, json.JSONDecodeError) as error:
                    print(f"    {station['name']} ÉCHEC : {error}", flush=True)
            if batch_start + batch_size < len(stations):
                time.sleep(10)


if __name__ == "__main__":
    main()
