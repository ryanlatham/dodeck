import os
from dataclasses import dataclass, field
from typing import List, Optional

from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _split_csv(value: str | None) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(slots=True)
class Settings:
    auth0_issuer: str = os.getenv("AUTH0_ISSUER", "").rstrip("/")
    auth0_audience: str = os.getenv("AUTH0_AUDIENCE", "")
    auth0_jwks_override_json: Optional[str] = os.getenv("AUTH0_JWKS_JSON")
    auth0_jwks_override_path: Optional[str] = os.getenv("AUTH0_JWKS_PATH")
    auth0_jwks_override_url: Optional[str] = os.getenv("AUTH0_JWKS_URL")

    require_email_verified: bool = field(default_factory=lambda: _bool(os.getenv("REQUIRE_EMAIL_VERIFIED"), True))
    table_name: str = os.getenv("TABLE_NAME", "DoDeck")
    cors_allowed_origins: List[str] = field(default_factory=lambda: _split_csv(os.getenv("CORS_ALLOWED_ORIGINS")))
    log_level: str = os.getenv("LOG_LEVEL", "info")
    aws_region: str = os.getenv("AWS_REGION", "us-west-2")
    dynamodb_endpoint_url: Optional[str] = os.getenv("DYNAMODB_ENDPOINT_URL")

    environment: str = os.getenv("ENVIRONMENT", "local")
    service_name: str = os.getenv("SERVICE_NAME", "dodeck-service")
    enable_xray_tracing: bool = field(default_factory=lambda: _bool(os.getenv("ENABLE_XRAY_TRACING"), False))
    xray_dynamic_naming: Optional[str] = os.getenv("XRAY_DYNAMIC_NAMING")


settings = Settings()
