from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict

import httpx
from fastapi import HTTPException, status
from jose import jwt
from jose.exceptions import JWTError

from .settings import settings

JWKS_CACHE: Dict[str, Dict[str, Any]] = {}
JWKS_EXPIRY: Dict[str, float] = {}


def _load_override() -> Dict[str, Any] | None:
    if settings.auth0_jwks_override_json:
        return json.loads(settings.auth0_jwks_override_json)
    if settings.auth0_jwks_override_path:
        path = Path(settings.auth0_jwks_override_path)
        if path.exists():
            return json.loads(path.read_text())
    if settings.auth0_jwks_override_url:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(settings.auth0_jwks_override_url, timeout=5.0)
            resp.raise_for_status()
            return resp.json()
    return None


def _get_jwks(issuer: str) -> Dict[str, Any]:
    now = time.time()
    if issuer in JWKS_CACHE and JWKS_EXPIRY.get(issuer, 0) > now:
        return JWKS_CACHE[issuer]

    override = _load_override()
    if override:
        JWKS_CACHE[issuer] = override
        JWKS_EXPIRY[issuer] = now + 300
        return override

    url = f"{issuer}/.well-known/jwks.json"
    with httpx.Client(timeout=5.0) as client:
        resp = client.get(url)
        resp.raise_for_status()
        jwks = resp.json()
    JWKS_CACHE[issuer] = jwks
    JWKS_EXPIRY[issuer] = now + 3600
    return jwks


def verify_jwt(authorization: str | None) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
        )

    if not settings.auth0_issuer or not settings.auth0_audience:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="server not configured",
        )

    token = authorization.split(" ", 1)[1]
    jwks = _get_jwks(settings.auth0_issuer)

    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        key = next((k for k in jwks["keys"] if k.get("kid") == kid), None)
        if not key:
            raise JWTError("no matching jwk")

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.auth0_audience,
            issuer=f"{settings.auth0_issuer}/",
        )
    except (JWTError, Exception) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token",
        ) from exc

    return payload
