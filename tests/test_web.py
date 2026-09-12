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


def test_catalog_and_unknown_station():
    client = create_app('sqlite://').test_client()
    stations = client.get('/api/stations').get_json()['stations']
    assert len({row['slug'] for row in stations}) == len(stations)
    assert {'Alpes', 'Pyrénées', 'Vosges', 'Jura', 'Massif central', 'Corse'} == {row['massif'] for row in stations}
    assert client.get('/api/snow-depth?station=unknown').status_code == 404
    assert client.get('/api/snow-depth?station=tignes').get_json()['seasons'] == {}


def test_import_uses_selected_coordinates_and_isolates_stations(tmp_path, monkeypatch):
    from snow_layers.stations import STATIONS_BY_SLUG
    from datetime import timedelta
    calls = []
    def fake_fetch(**kwargs):
        calls.append(kwargs)
        start, end = kwargs['start_date'], kwargs['end_date']
        return [(start + timedelta(days=i), 42) for i in range((end-start).days+1)], 'https://example.test/archive'
    monkeypatch.setattr('snow_layers.web.fetch_daily_snow_depth', fake_fetch)
    client = create_app(f"sqlite:///{tmp_path / 'stations.sqlite'}").test_client()
    body = {'station': 'tignes', 'season': '2024-2025'}
    response = client.post('/api/snow-depth/import', json=body)
    assert response.status_code == 200
    assert calls[0]['latitude'] == STATIONS_BY_SLUG['tignes']['latitude']
    assert calls[0]['longitude'] == STATIONS_BY_SLUG['tignes']['longitude']
    assert calls[0]['elevation_m'] == STATIONS_BY_SLUG['tignes']['elevation_m']
    assert client.post('/api/snow-depth/import', json=body).get_json()['cached'] is True
    assert len(calls) == 1
    payload = client.get('/api/snow-depth?station=tignes').get_json()
    assert payload['is_demo'] is False
    assert payload['collected_at']
    assert payload['seasons']['2024-2025'][0]['depth_cm'] == 42
    assert client.get('/api/snow-depth?station=meribel').get_json()['is_demo'] is True
    assert client.get('/api/snow-depth?station=avoriaz').get_json()['seasons'] == {}


def test_import_failure_and_invalid_requests(monkeypatch):
    import requests
    def fail(**kwargs):
        raise requests.Timeout()
    monkeypatch.setattr('snow_layers.web.fetch_daily_snow_depth', fail)
    client = create_app('sqlite://').test_client()
    for body in ([], {}, {'station': 'tignes', 'season': 'bad'}, {'station': 'tignes', 'season': '2099-2100'}):
        assert client.post('/api/snow-depth/import', json=body).status_code in (400, 404)
    assert client.post('/api/snow-depth/import', json={'station': 'tignes', 'season': '2024-2025'}).status_code == 502
    assert client.get('/api/snow-depth?station=tignes').get_json()['seasons'] == {}


def test_stations_have_altitude_categories_and_comparison_contract(tmp_path):
    from snow_layers.stations import STATIONS_BY_SLUG

    assert {station["altitude_category"] for station in STATIONS_BY_SLUG.values()} == {"basse", "moyenne", "haute"}
    client = create_app(f"sqlite:///{tmp_path / 'comparison.sqlite'}").test_client()
    response = client.get('/api/comparison?station=meribel&station=tignes')
    assert response.status_code == 200
    payload = response.get_json()
    assert set(payload["categories"]) == {"basse", "moyenne", "haute"}
    assert set(payload["stations"]) == {"meribel", "tignes"}
    assert client.get('/api/comparison?station=meribel').status_code == 400
