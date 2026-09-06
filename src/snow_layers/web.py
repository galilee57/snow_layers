"""Application Flask du prototype Méribel Snow Layers."""

from __future__ import annotations

from flask import Flask, jsonify, render_template

from snow_layers.database import create_session_factory
from snow_layers.demo_data import DEMO_SEASONS
from snow_layers.repository import load_seasons


def create_app(database_url: str | None = None) -> Flask:
    app = Flask(__name__, template_folder="../../templates", static_folder="../../static")
    app.config["SESSION_FACTORY"] = create_session_factory(database_url)

    @app.get("/")
    def index():
        return render_template("index.html", seasons=sorted(DEMO_SEASONS, reverse=True))

    @app.get("/api/snow-depth")
    def snow_depth():
        """Expose les observations importées, ou le jeu de démonstration initial."""
        with app.config["SESSION_FACTORY"]() as session:
            seasons = load_seasons(session)
        has_observations = bool(seasons)
        return jsonify(
            {
                "station": "Méribel",
                "unit": "cm",
                "source": (
                    "Open-Meteo Archive · ERA5-Land · hauteur de neige modélisée, moyenne quotidienne"
                    if has_observations
                    else "Données de démonstration — importez une saison Open-Meteo pour les remplacer"
                ),
                "is_demo": not has_observations,
                "seasons": seasons if has_observations else DEMO_SEASONS,
            }
        )

    return app
