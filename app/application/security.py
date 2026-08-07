from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.domain.auth import AuthenticatedUser
from app.domain.security import PasswordHasher, TokenService


class PBKDF2PasswordHasher(PasswordHasher):
    def __init__(self, iterations: int = 310_000) -> None:
        self._iterations = iterations

    def hash_password(self, password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, self._iterations)
        return "pbkdf2_sha256${iterations}${salt}${digest}".format(
            iterations=self._iterations,
            salt=base64.urlsafe_b64encode(salt).decode("ascii"),
            digest=base64.urlsafe_b64encode(digest).decode("ascii"),
        )

    def verify_password(self, password: str, password_hash: str) -> bool:
        try:
            algorithm, iterations, salt, digest = password_hash.split("$", 3)
            if algorithm != "pbkdf2_sha256":
                return False
            salt_bytes = base64.urlsafe_b64decode(salt.encode("ascii"))
            expected_digest = base64.urlsafe_b64decode(digest.encode("ascii"))
            candidate_digest = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt_bytes,
                int(iterations),
            )
            return hmac.compare_digest(candidate_digest, expected_digest)
        except (ValueError, TypeError):
            return False


class HMACTokenService(TokenService):
    def __init__(self, secret_key: str, issuer: str = "Cargo", expires_minutes: int = 60) -> None:
        self._secret_key = secret_key.encode("utf-8")
        self._issuer = issuer
        self._expires_minutes = expires_minutes

    def create_access_token(self, user: AuthenticatedUser) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user.user_id),
            "email": user.email,
            "admin": user.is_admin,
            "iss": self._issuer,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self._expires_minutes)).timestamp()),
        }
        header = {"alg": "HS256", "typ": "JWT"}
        header_segment = self._encode_segment(header)
        payload_segment = self._encode_segment(payload)
        signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
        signature = hmac.new(self._secret_key, signing_input, hashlib.sha256).digest()
        return f"{header_segment}.{payload_segment}.{self._base64url(signature)}"

    def parse_access_token(self, token: str) -> AuthenticatedUser:
        try:
            header_segment, payload_segment, signature_segment = token.split(".")
        except ValueError as exc:
            raise ValueError("Invalid token format") from exc

        signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
        expected_signature = hmac.new(self._secret_key, signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(expected_signature, self._decode_segment(signature_segment)):
            raise ValueError("Invalid token signature")

        payload = json.loads(self._decode_segment(payload_segment).decode("utf-8"))
        expires_at = datetime.fromtimestamp(int(payload["exp"]), tz=UTC)
        if expires_at < datetime.now(UTC):
            raise ValueError("Token expired")

        return AuthenticatedUser(
            user_id=UUID(payload["sub"]),
            email=payload["email"],
            is_admin=bool(payload.get("admin", False)),
        )

    def _encode_segment(self, value: dict[str, object]) -> str:
        raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return self._base64url(raw)

    def _base64url(self, value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")

    def _decode_segment(self, value: str) -> bytes:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def build_jwt_secret(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()
