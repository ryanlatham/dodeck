from typing import Dict


def auth_header(token: str) -> Dict[str, str]:
    return {"Authorization": token}


def test_owner_crud_and_collaboration_flow(test_client, token_factory):
    owner_token = token_factory("auth0|owner", "owner@example.com")
    collaborator_token = token_factory("auth0|collab", "collab@example.com")
    unverified_token = token_factory("auth0|collab2", "collab2@example.com", email_verified=False)

    # Owner creates a deck
    response = test_client.post(
        "/v1/decks",
        json={"name": "Focus Deck"},
        headers=auth_header(owner_token),
    )
    assert response.status_code == 201
    deck = response.json()
    deck_id = deck["deckId"]
    assert deck["isOwner"] is True
    assert deck["collaborators"] == []

    # Owner can fetch list and search
    response = test_client.get("/v1/decks", headers=auth_header(owner_token))
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["name"] == "Focus Deck"

    response = test_client.get(
        "/v1/decks",
        params={"search": "Foc"},
        headers=auth_header(owner_token),
    )
    assert response.status_code == 200
    assert response.json()["items"][0]["deckId"] == deck_id

    # Rename the deck
    response = test_client.patch(
        f"/v1/decks/{deck_id}",
        json={"name": "Focus Deck v2"},
        headers=auth_header(owner_token),
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Focus Deck v2"

    # Add collaborator
    response = test_client.post(
        f"/v1/decks/{deck_id}/collaborators",
        json={"email": "collab@example.com"},
        headers=auth_header(owner_token),
    )
    assert response.status_code == 201
    assert response.json()["collaborators"] == ["collab@example.com"]

    # Duplicate add results in 409
    response = test_client.post(
        f"/v1/decks/{deck_id}/collaborators",
        json={"email": "collab@example.com"},
        headers=auth_header(owner_token),
    )
    assert response.status_code == 409

    # Collaborator listing requires verified email
    response = test_client.get(
        "/v1/decks",
        params={"visibility": "shared"},
        headers=auth_header(unverified_token),
    )
    assert response.status_code == 403

    # Verified collaborator can list shared decks and access details
    response = test_client.get(
        "/v1/decks",
        params={"visibility": "shared"},
        headers=auth_header(collaborator_token),
    )
    shared_items = response.json()["items"]
    assert len(shared_items) == 1
    assert shared_items[0]["deckId"] == deck_id
    assert shared_items[0]["isOwner"] is False

    response = test_client.get(
        f"/v1/decks/{deck_id}",
        headers=auth_header(collaborator_token),
    )
    assert response.status_code == 200
    assert response.json()["isOwner"] is False

    # Collaborator cannot manage collaborators
    response = test_client.post(
        f"/v1/decks/{deck_id}/collaborators",
        json={"email": "another@example.com"},
        headers=auth_header(collaborator_token),
    )
    assert response.status_code == 403

    # Owner creates a Do item
    response = test_client.post(
        f"/v1/decks/{deck_id}/dos",
        json={"text": "First task"},
        headers=auth_header(owner_token),
    )
    assert response.status_code == 201
    do_item = response.json()
    do_id = do_item["doId"]
    assert do_item["completed"] is False

    # Collaborator can list and update the Do item
    response = test_client.get(
        f"/v1/decks/{deck_id}/dos",
        headers=auth_header(collaborator_token),
    )
    assert response.status_code == 200
    assert response.json()["items"][0]["doId"] == do_id

    response = test_client.patch(
        f"/v1/decks/{deck_id}/dos/{do_id}",
        json={"completed": True},
        headers=auth_header(collaborator_token),
    )
    assert response.status_code == 200
    assert response.json()["completed"] is True

    # Owner deletes Do
    response = test_client.delete(
        f"/v1/decks/{deck_id}/dos/{do_id}",
        headers=auth_header(owner_token),
    )
    assert response.status_code == 204

    # Delete collaborator
    response = test_client.delete(
        f"/v1/decks/{deck_id}/collaborators/collab@example.com",
        headers=auth_header(owner_token),
    )
    assert response.status_code == 204

    # Delete deck
    response = test_client.delete(
        f"/v1/decks/{deck_id}",
        headers=auth_header(owner_token),
    )
    assert response.status_code == 204

    response = test_client.get(
        "/v1/decks",
        headers=auth_header(owner_token),
    )
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_visibility_requires_email_claim(test_client, token_factory):
    token = token_factory("auth0|noemail", None)
    response = test_client.get(
        "/v1/decks",
        params={"visibility": "shared"},
        headers=auth_header(token),
    )
    assert response.status_code == 403


def test_requires_valid_email_for_collaborator_access(test_client, token_factory):
    owner_token = token_factory("auth0|owner2", "owner2@example.com")
    deck_id = test_client.post(
        "/v1/decks",
        json={"name": "Verifications"},
        headers=auth_header(owner_token),
    ).json()["deckId"]

    # Owner adds collaborator
    test_client.post(
        f"/v1/decks/{deck_id}/collaborators",
        json={"email": "verify@example.com"},
        headers=auth_header(owner_token),
    )

    unverified = token_factory("auth0|verify", "verify@example.com", email_verified=False)
    response = test_client.get(
        f"/v1/decks/{deck_id}",
        headers=auth_header(unverified),
    )
    assert response.status_code == 403
