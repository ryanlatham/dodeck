def test_requires_auth_on_decks(test_client):
    response = test_client.get("/v1/decks")
    assert response.status_code == 401
