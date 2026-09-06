from datetime import date

from snow_layers.database import create_session_factory
from snow_layers.open_meteo import SOURCE_NAME
from snow_layers.repository import get_or_create_meribel, upsert_observations
from snow_layers.web import create_app


def test_home_page_is_available():
    response = create_app().test_client().get("/")

    assert response.status_code == 200
    assert "Méribel" in response.get_data(as_text=True)


def test_snow_depth_api_exposes_demo_contract():
    response = create_app("sqlite://").test_client().get("/api/snow-depth")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["unit"] == "cm"
    assert "2025-2026" in payload["seasons"]


def test_snow_depth_api_reads_imported_observations(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'snow.sqlite'}"
    session_factory = create_session_factory(database_url)
    with session_factory.begin() as session:
        station = get_or_create_meribel(session)
        upsert_observations(
            session,
            station=station,
            records=[(date(2024, 12, 1), 44.5)],
            source=SOURCE_NAME,
            source_url="https://example.test/open-meteo",
        )

    response = create_app(database_url).test_client().get("/api/snow-depth")
    payload = response.get_json()

    assert payload["is_demo"] is False
    assert payload["seasons"]["2024-2025"] == [{"date": "2024-12-01", "depth_cm": 44.5}]
