from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_advance_windows_endpoint():
    response = client.get("/api/v1/index/advance-windows")
    assert response.status_code == 200
    assert response.json() == {"windows": [1, 7, 15, 30, 45]}


def _all_registered_paths() -> set[str]:
    """FastAPI's OpenAPI schema already flattens included sub-routers into
    concrete paths, so it's a more reliable source of truth here than
    walking app.routes (whose entries for included routers don't expose a
    .path attribute directly).
    """
    return set(app.openapi()["paths"].keys())


def test_index_routes_registered():
    paths = _all_registered_paths()
    assert "/api/v1/index" in paths
    assert "/api/v1/index/routes" in paths
    assert "/api/v1/index/advance-windows" in paths


def test_scraping_routes_registered():
    paths = _all_registered_paths()
    assert "/api/v1/scraping/route/{route_code}" in paths
    assert "/api/v1/scraping/jobs/{job_id}" in paths


def test_fares_routes_registered():
    paths = _all_registered_paths()
    assert "/api/v1/fares" in paths


def test_index_summary_schema_fields():
    from app.schemas.index import IndexSummaryOut

    fields = IndexSummaryOut.model_fields
    assert "date" in fields
    assert "index" in fields
    assert "base" in fields
    assert "advance_windows" in fields


def test_route_index_schema_fields():
    from app.schemas.index import RouteIndexOut

    fields = RouteIndexOut.model_fields
    assert "route_id" in fields
    assert "route_code" in fields
    assert "index_value" in fields
    assert "base_value" in fields
