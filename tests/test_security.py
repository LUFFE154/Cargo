from __future__ import annotations

from uuid import uuid4

from app.application.security import HMACTokenService, PBKDF2PasswordHasher
from app.domain.auth import AuthenticatedUser


def test_password_hasher_round_trip() -> None:
    hasher = PBKDF2PasswordHasher(iterations=10_000)
    password_hash = hasher.hash_password("correct horse battery staple")

    assert hasher.verify_password("correct horse battery staple", password_hash)
    assert not hasher.verify_password("incorrect", password_hash)


def test_hmac_token_service_round_trip() -> None:
    service = HMACTokenService(secret_key="secret", issuer="Cargo", expires_minutes=5)
    user = AuthenticatedUser(user_id=uuid4(), email="user@example.com", is_admin=True)

    token = service.create_access_token(user)
    parsed = service.parse_access_token(token)

    assert parsed.user_id == user.user_id
    assert parsed.email == user.email
    assert parsed.is_admin is True
