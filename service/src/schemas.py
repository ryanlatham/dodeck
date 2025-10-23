from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, constr


def utc_now() -> datetime:
    return datetime.utcnow()


class DeckCreateRequest(BaseModel):
    name: constr(min_length=1, max_length=120) = Field(..., description="Deck name")


class DeckRenameRequest(BaseModel):
    name: constr(min_length=1, max_length=120)


class DeckSummary(BaseModel):
    deckId: str
    name: str
    isOwner: bool
    collaborators: int = 0


class DeckDetail(BaseModel):
    deckId: str
    name: str
    isOwner: bool
    ownerSub: str
    collaborators: List[str]
    createdAt: datetime
    updatedAt: datetime


class CollaboratorAddRequest(BaseModel):
    email: EmailStr


class DoCreateRequest(BaseModel):
    text: constr(min_length=1, max_length=1000)


class DoUpdateRequest(BaseModel):
    text: Optional[constr(min_length=1, max_length=1000)] = None
    completed: Optional[bool] = None


class DoItem(BaseModel):
    doId: str
    deckId: str
    text: str
    completed: bool
    createdAt: datetime
    updatedAt: datetime
