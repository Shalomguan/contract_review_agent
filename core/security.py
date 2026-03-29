from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode('ascii')


def _b64url_decode(value: str) -> bytes:
    padding = '=' * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode('ascii'))


class PasswordHasher:
    """Hash and verify passwords with PBKDF2-HMAC."""

    algorithm = 'pbkdf2_sha256'
    iterations = 200000

    def hash_password(self, password: str) -> str:
        salt = os.urandom(16)
        digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, self.iterations)
        return f'{self.algorithm}${self.iterations}${salt.hex()}${digest.hex()}'

    def verify_password(self, password: str, stored_hash: str) -> bool:
        try:
            algorithm, iteration_text, salt_hex, digest_hex = stored_hash.split('$', 3)
        except ValueError:
            return False
        if algorithm != self.algorithm:
            return False
        iterations = int(iteration_text)
        expected = bytes.fromhex(digest_hex)
        candidate = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            bytes.fromhex(salt_hex),
            iterations,
        )
        return hmac.compare_digest(candidate, expected)


@dataclass(slots=True)
class TokenPayload:
    user_id: str
    username: str
    expires_at: datetime


class TokenManager:
    """Issue and validate signed bearer tokens."""

    def __init__(self, secret_key: str, ttl_minutes: int) -> None:
        self.secret_key = secret_key.encode('utf-8')
        self.ttl_minutes = ttl_minutes

    def issue_token(self, user_id: str, username: str) -> str:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.ttl_minutes)
        payload = {
            'sub': user_id,
            'username': username,
            'exp': int(expires_at.timestamp()),
        }
        payload_segment = _b64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
        signature = hmac.new(self.secret_key, payload_segment.encode('ascii'), hashlib.sha256).digest()
        return f'{payload_segment}.{_b64url_encode(signature)}'

    def verify_token(self, token: str) -> TokenPayload | None:
        try:
            payload_segment, signature_segment = token.split('.', 1)
        except ValueError:
            return None

        expected_signature = hmac.new(
            self.secret_key,
            payload_segment.encode('ascii'),
            hashlib.sha256,
        ).digest()
        try:
            provided_signature = _b64url_decode(signature_segment)
        except Exception:
            return None
        if not hmac.compare_digest(expected_signature, provided_signature):
            return None

        try:
            payload = json.loads(_b64url_decode(payload_segment).decode('utf-8'))
        except Exception:
            return None

        expires_at = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
        if expires_at <= datetime.now(timezone.utc):
            return None

        return TokenPayload(
            user_id=payload['sub'],
            username=payload['username'],
            expires_at=expires_at,
        )
