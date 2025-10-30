from hashlib import sha256

from fastapi.testclient import TestClient

from app.models.database import AnalysisHistory


def test_analyze_code_persists_and_caches(
    client: TestClient,
    db_session,
    cache_service,
) -> None:
    payload = {"code": "def foo():\n    return 1\n", "language_version": "3.11"}

    response = client.post("/api/v1/analyze-code", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["cached"] is False
    assert body["code_hash"] == sha256(payload["code"].encode()).hexdigest()
    assert isinstance(body["suggestions"], list)

    stored = (
        db_session.query(AnalysisHistory)
        .filter_by(code_hash=body["code_hash"])
        .one()
    )
    assert stored.code_snippet == payload["code"]
    assert f"analysis:{body['code_hash']}" in cache_service.store


def test_analyze_code_returns_cached_response(client: TestClient, cache_service) -> None:
    payload = {"code": "print('hi')\n", "language_version": "3.11"}
    code_hash = sha256(payload["code"].encode()).hexdigest()
    cached_payload = {
        "code_hash": code_hash,
        "suggestions": [],
        "analysis_time_ms": 1,
    }
    cache_service.store[f"analysis:{code_hash}"] = cached_payload

    response = client.post("/api/v1/analyze-code", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body == {**cached_payload, "cached": True}


def test_health_endpoint_reports_dependencies(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["cache"] in {"ok", "fallback"}

