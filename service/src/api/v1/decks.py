from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from ...dependencies import AuthContext, get_current_user
from ...repository import (
    CollaboratorNotFoundError,
    DuplicateCollaboratorError,
    add_collaborator,
    batch_load_decks,
    create_deck,
    delete_deck,
    get_deck,
    get_do,
    list_access_rows,
    list_dos,
    remove_collaborator,
    rename_deck,
    create_do,
    update_do,
    delete_do,
)
from ...schemas import (
    CollaboratorAddRequest,
    DeckCreateRequest,
    DeckDetail,
    DeckRenameRequest,
    DeckSummary,
    DoCreateRequest,
    DoItem,
    DoUpdateRequest,
)

router = APIRouter(prefix="/v1/decks", tags=["decks"])


def _collaborator_list(deck: Dict) -> List[str]:
    collaborators = deck.get("collaborators") or {}
    return sorted(collaborators.keys())


def _deck_to_summary(deck: Dict, user: AuthContext) -> DeckSummary:
    return DeckSummary(
        deckId=deck["deckId"],
        name=deck["name"],
        isOwner=deck["ownerSub"] == user.sub,
        collaborators=len(_collaborator_list(deck)),
    )


def _deck_to_detail(deck: Dict, user: AuthContext) -> DeckDetail:
    return DeckDetail(
        deckId=deck["deckId"],
        name=deck["name"],
        isOwner=deck["ownerSub"] == user.sub,
        ownerSub=deck["ownerSub"],
        collaborators=_collaborator_list(deck),
        createdAt=deck["createdAt"],
        updatedAt=deck["updatedAt"],
    )


def _ensure_access(deck: Dict, user: AuthContext, *, require_owner: bool = False):
    if deck["ownerSub"] == user.sub:
        return
    if require_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="owner_only")
    email = user.require_email()
    collaborators = deck.get("collaborators") or {}
    if email not in collaborators:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")


@router.get("", response_model=Dict[str, List[DeckSummary]])
def list_decks_endpoint(
    search: Optional[str] = Query(None),
    visibility: str = Query("all", pattern="^(mine|shared|all)$"),
    user: AuthContext = Depends(get_current_user),
):
    if visibility not in {"mine", "shared", "all"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid_visibility")

    if visibility in {"shared", "all"}:
        user.require_email()

    access_rows = list_access_rows(user.sub, user.email if user.email_verified else None, visibility, search)
    deck_map = batch_load_decks(row["deckId"] for row in access_rows)

    summaries: List[DeckSummary] = []
    for row in access_rows:
        deck = deck_map.get(row["deckId"])
        if not deck:
            continue
        summaries.append(_deck_to_summary(deck, user))

    summaries.sort(key=lambda d: (not d.isOwner, d.name.lower()))
    return {"items": summaries}


@router.post("", response_model=DeckDetail, status_code=status.HTTP_201_CREATED)
def create_deck_endpoint(
    payload: DeckCreateRequest,
    user: AuthContext = Depends(get_current_user),
):
    deck = create_deck(user.sub, payload.name)
    return _deck_to_detail(deck, user)


def _get_deck_or_404(deck_id: str) -> Dict:
    deck = get_deck(deck_id)
    if not deck:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="deck_not_found")
    return deck


@router.get("/{deck_id}", response_model=DeckDetail)
def get_deck_endpoint(deck_id: str, user: AuthContext = Depends(get_current_user)):
    deck = _get_deck_or_404(deck_id)
    _ensure_access(deck, user)
    return _deck_to_detail(deck, user)


@router.patch("/{deck_id}", response_model=DeckDetail)
def rename_deck_endpoint(
    deck_id: str,
    payload: DeckRenameRequest,
    user: AuthContext = Depends(get_current_user),
):
    deck = _get_deck_or_404(deck_id)
    _ensure_access(deck, user, require_owner=True)
    updated = rename_deck(deck, payload.name)
    return _deck_to_detail(updated, user)


@router.delete("/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deck_endpoint(deck_id: str, user: AuthContext = Depends(get_current_user)):
    deck = _get_deck_or_404(deck_id)
    _ensure_access(deck, user, require_owner=True)
    delete_deck(deck)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{deck_id}/collaborators", response_model=DeckDetail, status_code=status.HTTP_201_CREATED)
def add_collaborator_endpoint(
    deck_id: str,
    payload: CollaboratorAddRequest,
    user: AuthContext = Depends(get_current_user),
):
    deck = _get_deck_or_404(deck_id)
    _ensure_access(deck, user, require_owner=True)
    email = payload.email.lower()
    if user.email and user.email == email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cannot_add_self")
    try:
        updated = add_collaborator(deck, email)
    except DuplicateCollaboratorError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="collaborator_exists")
    return _deck_to_detail(updated, user)


@router.delete("/{deck_id}/collaborators/{email}", status_code=status.HTTP_204_NO_CONTENT)
def remove_collaborator_endpoint(
    deck_id: str,
    email: str,
    user: AuthContext = Depends(get_current_user),
):
    deck = _get_deck_or_404(deck_id)
    _ensure_access(deck, user, require_owner=True)
    email_lower = email.lower()
    try:
        remove_collaborator(deck, email_lower)
    except CollaboratorNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="collaborator_not_found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _deck_access_for_dos(deck_id: str, user: AuthContext) -> Dict:
    deck = _get_deck_or_404(deck_id)
    _ensure_access(deck, user)
    return deck


@router.get("/{deck_id}/dos", response_model=Dict[str, List[DoItem]])
def list_dos_endpoint(deck_id: str, user: AuthContext = Depends(get_current_user)):
    _deck_access_for_dos(deck_id, user)
    items = list_dos(deck_id)
    dos = [
        DoItem(
            doId=item["doId"],
            deckId=item["deckId"],
            text=item["text"],
            completed=item.get("completed", False),
            createdAt=item["createdAt"],
            updatedAt=item["updatedAt"],
        )
        for item in items
    ]
    dos.sort(key=lambda d: d.createdAt)
    return {"items": dos}


@router.post("/{deck_id}/dos", response_model=DoItem, status_code=status.HTTP_201_CREATED)
def create_do_endpoint(
    deck_id: str,
    payload: DoCreateRequest,
    user: AuthContext = Depends(get_current_user),
):
    _deck_access_for_dos(deck_id, user)
    do_item = create_do(deck_id, payload.text)
    return DoItem(
        doId=do_item["doId"],
        deckId=deck_id,
        text=do_item["text"],
        completed=do_item["completed"],
        createdAt=do_item["createdAt"],
        updatedAt=do_item["updatedAt"],
    )


@router.patch("/{deck_id}/dos/{do_id}", response_model=DoItem)
def update_do_endpoint(
    deck_id: str,
    do_id: str,
    payload: DoUpdateRequest,
    user: AuthContext = Depends(get_current_user),
):
    _deck_access_for_dos(deck_id, user)
    if payload.text is None and payload.completed is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="no_updates_provided")

    existing = get_do(deck_id, do_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="do_not_found")

    updated = update_do(existing, payload.text, payload.completed)
    return DoItem(
        doId=updated["doId"],
        deckId=updated["deckId"],
        text=updated["text"],
        completed=updated["completed"],
        createdAt=updated["createdAt"],
        updatedAt=updated["updatedAt"],
    )


@router.delete("/{deck_id}/dos/{do_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_do_endpoint(deck_id: str, do_id: str, user: AuthContext = Depends(get_current_user)):
    _deck_access_for_dos(deck_id, user)
    delete_do(deck_id, do_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
