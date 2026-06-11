"""Authentication wiring tests."""

from app.core.auth import create_access_token, decode_access_token
from app.main import app


def test_auth_routes_are_registered() -> None:
    paths = {getattr(route, "path", "") for route in app.routes}

    assert "/api/v1/auth/google" in paths
    assert "/api/v1/auth/me" in paths


def test_access_token_round_trip() -> None:
    token = create_access_token("u1", "user@example.com", "User")

    payload = decode_access_token(token)

    assert payload["sub"] == "u1"
    assert payload["email"] == "user@example.com"


def test_auth_me_requires_token(client) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
