"""Commande d'import de la hauteur de neige historique Open-Meteo.

Usage : PYTHONPATH=src .venv/bin/python -m snow_layers.import_open_meteo --season 2024-2025
"""

from __future__ import annotations

import argparse
from datetime import date

from snow_layers.database import create_session_factory
from snow_layers.open_meteo import SOURCE_NAME, fetch_daily_snow_depth
from snow_layers.repository import get_or_create_station, upsert_observations
from snow_layers.stations import STATIONS_BY_SLUG


def parse_season(value: str) -> tuple[date, date]:
    try:
        start_year, end_year = (int(part) for part in value.split("-"))
    except ValueError as error:
        raise argparse.ArgumentTypeError("La saison doit respecter le format AAAA-AAAA.") from error
    if end_year != start_year + 1:
        raise argparse.ArgumentTypeError("Une saison doit couvrir deux années consécutives.")
    return date(start_year, 12, 1), date(end_year, 4, 30)


def main() -> None:
    parser = argparse.ArgumentParser(description="Importe une saison de neige de Méribel depuis Open-Meteo.")
    parser.add_argument("--season", required=True, type=parse_season, help="Ex. 2024-2025")
    parser.add_argument("--station", choices=sorted(STATIONS_BY_SLUG), default="meribel")
    args = parser.parse_args()
    definition = STATIONS_BY_SLUG[args.station]
    start_date, end_date = args.season
    records, source_url = fetch_daily_snow_depth(
        latitude=definition["latitude"],
        longitude=definition["longitude"],
        elevation_m=definition["elevation_m"],
        start_date=start_date,
        end_date=end_date,
    )
    session_factory = create_session_factory()
    with session_factory.begin() as session:
        station = get_or_create_station(session, definition)
        count = upsert_observations(session, station=station, records=records, source=SOURCE_NAME, source_url=source_url)
    print(f"{count} jours importés pour {definition['name']} ({start_date} → {end_date}).")


if __name__ == "__main__":
    main()
