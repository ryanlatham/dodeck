import json
import os
import sys
from datetime import datetime, timedelta, timezone
from importlib import reload
from pathlib import Path
from typing import Callable, Generator

import boto3
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from jose import jwt
from jose.utils import base64url_encode

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

ISSUER = "https://test.auth0.com"
AUDIENCE = "dodeck-api"
KEY_ID = "test-key"
TABLE_NAME = os.getenv("TABLE_NAME", "DoDeck")

# Generate RSA key pair for tests
_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_public_numbers = _private_key.public_key().public_numbers()

_e = base64url_encode(
    _public_numbers.e.to_bytes(
        (_public_numbers.e.bit_length() + 7) // 8, byteorder="big"
    )
).decode("utf-8")
_n = base64url_encode(
    _public_numbers.n.to_bytes(
        (_public_numbers.n.bit_length() + 7) // 8, byteorder="big"
    )
).decode("utf-8")

JWKS = {
    "keys": [
        {
            "kty": "RSA",
            "use": "sig",
            "kid": KEY_ID,
            "alg": "RS256",
            "n": _n,
            "e": _e,
        }
    ]
}

os.environ.setdefault("AUTH0_ISSUER", ISSUER)
os.environ.setdefault("AUTH0_AUDIENCE", AUDIENCE)
os.environ["AUTH0_JWKS_JSON"] = json.dumps(JWKS)
os.environ.setdefault("AWS_REGION", "us-west-2")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("DYNAMODB_ENDPOINT_URL", "http://localhost:8000")
os.environ.setdefault("REQUIRE_EMAIL_VERIFIED", "true")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("TABLE_NAME", TABLE_NAME)


@pytest.fixture(scope="session", autouse=True)
def reload_settings() -> None:
    import src.settings as settings_module
    import src.security as security_module

    reload(settings_module)
    reload(security_module)
    security_module.JWKS_CACHE.clear()
    security_module.JWKS_EXPIRY.clear()


@pytest.fixture(scope="session")
def test_client() -> Generator[TestClient, None, None]:
    from src.main import app as fastapi_app

    with TestClient(fastapi_app) as client:
        yield client


@pytest.fixture(scope="session")
def dynamodb_table() -> Generator:
    resource = boto3.resource(
        "dynamodb",
        region_name=os.environ["AWS_REGION"],
        endpoint_url=os.environ["DYNAMODB_ENDPOINT_URL"],
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )

    table = resource.Table(TABLE_NAME)
    try:
        table.load()
    except resource.meta.client.exceptions.ResourceNotFoundException:
        table = resource.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
    return table


def _wipe_table(table) -> None:
    scan = table.scan()
    with table.batch_writer() as batch:
        for item in scan.get("Items", []):
            batch.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})
    while "LastEvaluatedKey" in scan:
        scan = table.scan(ExclusiveStartKey=scan["LastEvaluatedKey"])
        with table.batch_writer() as batch:
            for item in scan.get("Items", []):
                batch.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})


@pytest.fixture(autouse=True)
def clean_table(dynamodb_table):
    _wipe_table(dynamodb_table)
    yield
    _wipe_table(dynamodb_table)


@pytest.fixture
def token_factory() -> Callable[[str, str | None, bool], str]:
    def _make(sub: str, email: str | None, email_verified: bool = True, **claims) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": sub,
            "iss": f"{ISSUER}/",
            "aud": AUDIENCE,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
        }
        if email:
            payload["https://dodeck.app/email"] = email.lower()
            payload["https://dodeck.app/email_verified"] = email_verified
        payload.update(claims)

        private_pem = _private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        token = jwt.encode(
            payload,
            private_pem,
            algorithm="RS256",
            headers={"kid": KEY_ID},
        )
        return f"Bearer {token}"

    return _make
