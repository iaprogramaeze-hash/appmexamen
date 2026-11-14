"""Health check (S6): 200 siempre, degradación de db y CORS según settings."""
from __future__ import annotations

from fastapi.testclient import TestClient
from starlette.middleware.cors import CORSMiddleware

from app.core.config import Settings
from app.main import create_app


def test_healthz_without_database_degrades():
    app = create_app(Settings(_env_file=None, environment="test"))
    with TestClient(app) as client:
        body = client.get("/healthz")
    assert body.status_code == 200
    data = body.json()
    assert data["status"] == "ok"
    assert data["environment"] == "test"
    assert data["db"] == "unavailable"


def test_healthz_with_sqlite_ok():
    app = create_app(
        Settings(_env_file=None, environment="test", database_url="sqlite+aiosqlite:///:memory:")
    )
    with TestClient(app) as client:
        body = client.get("/healthz")
    assert body.status_code == 200
    assert body.json()["db"] == "ok"


def test_cors_disabled_by_default():
    app = create_app(Settings(_env_file=None, environment="test"))
    assert not any(m.cls is CORSMiddleware for m in app.user_middleware)


def test_cors_enabled_with_origins():
    app = create_app(
        Settings(_env_file=None, environment="test", cors_origins=["https://landing.example.com"])
    )
    assert any(m.cls is CORSMiddleware for m in app.user_middleware)


def test_api_v1_prefix_applied_by_factory():
    """create_app monta api_router bajo /api/v1 (analisis.txt 5) y /healthz en raíz."""
    from app.api.v1.api import api_router

    before = list(api_router.routes)

    @api_router.get("/prueba-prefijo", tags=["prueba"])
    def _prueba() -> dict[str, bool]:
        return {"ok": True}

    try:
        app = create_app(Settings(_env_file=None, environment="test"))
        paths = app.openapi()["paths"]
        assert "/healthz" in paths
        assert "/api/v1/prueba-prefijo" in paths
    finally:
        api_router.routes[:] = before
