def test_healthz(test_client):
    response = test_client.get("/healthz")
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("ok") is True
    assert payload.get("version") == "1.0.0"
