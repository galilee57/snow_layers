"""Persistance et lecture des séries de neige pour l'application."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from snow_layers.models import SnowObservation, Station


MERIBEL = {
    "slug": "meribel",
    "name": "Méribel",
    "latitude": 45.41497,
    "longitude": 6.5650,
    "elevation_m": 1450.0,
}


def get_or_create_station(session: Session, definition: dict) -> Station:
    station = session.scalar(select(Station).where(Station.slug == definition["slug"]))
    if station is None:
        station = Station(**{key: definition[key] for key in MERIBEL})
        session.add(station)
        session.flush()
    return station


def get_or_create_meribel(session: Session) -> Station:
    return get_or_create_station(session, MERIBEL)


def upsert_observations(
    session: Session, *, station: Station, records: list[tuple[date, float]], source: str, source_url: str
) -> int:
    existing = {
        observed_on: observation
        for observed_on, observation in session.execute(
            select(SnowObservation.observed_on, SnowObservation).where(
                SnowObservation.station_id == station.id, SnowObservation.source == source
            )
        )
    }
    for observed_on, snow_depth_cm in records:
        observation = existing.get(observed_on)
        if observation is None:
            session.add(
                SnowObservation(
                    station_id=station.id,
                    observed_on=observed_on,
                    snow_depth_cm=snow_depth_cm,
                    source=source,
                    source_url=source_url,
                )
            )
        else:
            observation.snow_depth_cm = snow_depth_cm
            observation.source_url = source_url
    return len(records)


def season_for(day: date) -> str:
    start_year = day.year if day.month >= 7 else day.year - 1
    return f"{start_year}-{start_year + 1}"


def load_seasons(session: Session, station_slug: str = "meribel") -> dict[str, list[dict[str, str | float]]]:
    rows = session.execute(
        select(SnowObservation).join(Station).where(Station.slug == station_slug).order_by(SnowObservation.observed_on)
    ).scalars()
    seasons: dict[str, list[dict[str, str | float]]] = {}
    for observation in rows:
        # Une saison comparative couvre l'hiver météorologique retenu par
        # l'import : décembre à avril. Les gros téléchargements historiques
        # peuvent aussi contenir les mois d'été entre deux hivers.
        if observation.observed_on.month not in (12, 1, 2, 3, 4):
            continue
        seasons.setdefault(season_for(observation.observed_on), []).append(
            {"date": observation.observed_on.isoformat(), "depth_cm": observation.snow_depth_cm}
        )
    return seasons
