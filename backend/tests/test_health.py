def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "creatorlens-api"}


def test_service_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["health"] == "/api/health"
