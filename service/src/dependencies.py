from dataclasses import dataclass
from typing import Any, Dict, Optional

from fastapi import Depends, Header, HTTPException, status

from .security import verify_jwt
from .settings import settings


@dataclass(slots=True)
class AuthContext:
    sub: str
    email: Optional[str]
    email_verified: bool
    claims: Dict[str, Any]

    def require_email(self) -> str:
        if not self.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="email_required",
            )
        if settings.require_email_verified and not self.email_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="email_not_verified",
            )
        return self.email


def get_current_user(authorization: str | None = Header(default=None)) -> AuthContext:
    claims = verify_jwt(authorization)
    sub = claims.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_token",
        )

    email = (
        claims.get("https://dodeck.app/email")
        or claims.get("email")
        or None
    )
    if isinstance(email, str):
        email = email.lower()
    else:
        email = None

    email_verified = bool(
        claims.get("https://dodeck.app/email_verified")
        if "https://dodeck.app/email_verified" in claims
        else claims.get("email_verified")
    )

    return AuthContext(
        sub=sub,
        email=email,
        email_verified=email_verified,
        claims=claims,
    )


def require_verified_collaborator(user: AuthContext = Depends(get_current_user)) -> AuthContext:
    user.require_email()
    return user
