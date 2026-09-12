"""Application Flask de sélection des stations et d'analyse d'enneigement."""
from __future__ import annotations

from datetime import date
import argparse
import requests
from flask import Flask, jsonify, render_template, request
from sqlalchemy import select

from snow_layers.database import create_session_factory
from snow_layers.demo_data import DEMO_SEASONS
from snow_layers.import_open_meteo import parse_season
from snow_layers.models import SnowObservation, Station
from snow_layers.open_meteo import SOURCE_NAME, fetch_daily_snow_depth
from snow_layers.repository import get_or_create_station, load_seasons, upsert_observations
from snow_layers.stations import STATIONS, STATIONS_BY_SLUG, CATALOG_NOTE


def _comparison_payload(session, selected_slugs: list[str]) -> dict:
    """Construit les moyennes saisonnières station et catégorie en centimètres."""
    by_station = {station["slug"]: load_seasons(session, station["slug"]) for station in STATIONS}
    all_seasons = sorted({season for seasons in by_station.values() for season in seasons}, reverse=False)
    station_means = {}
    for station in STATIONS:
        station_means[station["slug"]] = {
            season: round(sum(row["depth_cm"] for row in rows) / len(rows), 1)
            for season, rows in by_station[station["slug"]].items() if rows
        }
    categories = {}
    for category in ("basse", "moyenne", "haute"):
        members = [station["slug"] for station in STATIONS if station["altitude_category"] == category]
        categories[category] = {}
        for season in all_seasons:
            values = [station_means[slug][season] for slug in members if season in station_means[slug]]
            if values:
                categories[category][season] = {
                    "min": round(min(values), 1), "max": round(max(values), 1),
                    "mean": round(sum(values) / len(values), 1), "count": len(values),
                }
    return {
        "unit": "cm", "seasons": all_seasons,
        "stations": {
            slug: {"name": STATIONS_BY_SLUG[slug]["name"], "category": STATIONS_BY_SLUG[slug]["altitude_category"], "values": station_means[slug]}
            for slug in selected_slugs
        },
        "categories": categories,
    }


def create_app(database_url: str | None = None) -> Flask:
    app = Flask(__name__, template_folder='../../templates', static_folder='../../static')
    app.config['SESSION_FACTORY'] = create_session_factory(database_url)

    @app.get('/')
    def index():
        year = date.today().year - (date.today().month < 5)
        return render_template('index.html', import_seasons=[f'{y-1}-{y}' for y in range(year, year-10, -1)])

    @app.get('/api/stations')
    def stations():
        return jsonify(stations=STATIONS, note=CATALOG_NOTE)

    @app.get('/api/snow-depth')
    def snow_depth():
        slug = request.args.get('station', 'meribel')
        definition = STATIONS_BY_SLUG.get(slug)
        if definition is None:
            return jsonify(error='Station inconnue.'), 404
        with app.config['SESSION_FACTORY']() as session:
            seasons = load_seasons(session, slug)
            latest = session.scalar(select(SnowObservation.imported_at).join(Station).where(
                Station.slug == slug).order_by(SnowObservation.imported_at.desc()).limit(1))
        is_demo = not seasons and slug == 'meribel'
        return jsonify(station=definition['name'], station_slug=slug,
                       location=definition, unit='cm', is_demo=is_demo,
                       source=SOURCE_NAME if seasons else ('Données de démonstration · simulées' if is_demo else 'Aucune donnée locale pour cette station.'),
                       collected_at=latest.isoformat() if latest else None,
                       seasons=seasons or (DEMO_SEASONS if is_demo else {}))

    @app.get('/api/comparison')
    def comparison():
        requested = request.args.getlist('station')
        if len(requested) == 1 and ',' in requested[0]:
            requested = requested[0].split(',')
        selected = [slug for slug in dict.fromkeys(requested) if slug in STATIONS_BY_SLUG]
        if len(selected) != 2:
            return jsonify(error='Sélectionnez exactement deux stations.'), 400
        with app.config['SESSION_FACTORY']() as session:
            return jsonify(_comparison_payload(session, selected))

    @app.post('/api/snow-depth/import')
    def import_depth():
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify(error='Requête JSON attendue.'), 400
        slug, season = body.get('station'), body.get('season')
        definition = STATIONS_BY_SLUG.get(slug) if isinstance(slug, str) else None
        if definition is None:
            return jsonify(error='Station inconnue.'), 404
        try:
            if not isinstance(season, str):
                raise ValueError()
            start, end = parse_season(season)
            if start.year < 1950 or end >= date.today():
                raise ValueError()
        except (ValueError, argparse.ArgumentTypeError):
            return jsonify(error='Choisissez une saison terminée, depuis 1950, au format AAAA-AAAA.'), 400
        with app.config['SESSION_FACTORY']() as session:
            cached = load_seasons(session, slug).get(season, [])
        if len(cached) == (end-start).days + 1 and cached[0]['date'] == start.isoformat() and cached[-1]['date'] == end.isoformat():
            return jsonify(cached=True, count=len(cached))
        try:
            records, source_url = fetch_daily_snow_depth(
                latitude=definition['latitude'], longitude=definition['longitude'],
                elevation_m=definition['elevation_m'], start_date=start, end_date=end)
            if not records:
                return jsonify(error='Open-Meteo ne renvoie aucune donnée pour cette période.'), 502
        except (requests.RequestException, KeyError, ValueError, TypeError):
            return jsonify(error='Open-Meteo est indisponible. Réessayez plus tard ; les données locales sont conservées.'), 502
        with app.config['SESSION_FACTORY'].begin() as session:
            station = get_or_create_station(session, definition)
            upsert_observations(session, station=station, records=records, source=SOURCE_NAME, source_url=source_url)
        return jsonify(cached=False, count=len(records), partial=len(records) != (end-start).days+1)

    return app
