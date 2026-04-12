from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthcheck():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "plantpal-backend"


def test_docs_accessible():
    resp = client.get("/docs")
    assert resp.status_code == 200


def test_openapi_accessible():
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
