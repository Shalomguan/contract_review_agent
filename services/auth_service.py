from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from core.security import PasswordHasher, TokenManager, TokenPayload
from models.user import User
from repositories.user_repository import UserRepository


class AuthenticationError(Exception):
    """Raised when user authentication fails."""


class RegistrationError(Exception):
    """Raised when user registration fails."""


@dataclass(slots=True)
class AuthResult:
    """Authenticated session payload."""

    access_token: str
    token_type: str
    user: User


class AuthService:
    """Register, authenticate, and resolve users."""

    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        token_manager: TokenManager,
    ) -> None:
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.token_manager = token_manager

    def register(self, username: str, password: str) -> AuthResult:
        normalized_username = self._normalize_username(username)
        self._validate_password(password)
        password_hash = self.password_hasher.hash_password(password)
        try:
            user = self.user_repository.create(normalized_username, password_hash)
        except sqlite3.IntegrityError as exc:
            raise RegistrationError('用户名已存在。') from exc
        return self._build_auth_result(user)

    def login(self, username: str, password: str) -> AuthResult:
        normalized_username = self._normalize_username(username)
        user = self.user_repository.get_by_username(normalized_username)
        if user is None or not self.password_hasher.verify_password(password, user.password_hash):
            raise AuthenticationError('用户名或密码错误。')
        return self._build_auth_result(user)

    def get_current_user(self, token: str) -> User:
        payload = self.token_manager.verify_token(token)
        if payload is None:
            raise AuthenticationError('登录状态已失效，请重新登录。')
        user = self.user_repository.get_by_id(payload.user_id)
        if user is None:
            raise AuthenticationError('当前用户不存在。')
        return user

    def _build_auth_result(self, user: User) -> AuthResult:
        return AuthResult(
            access_token=self.token_manager.issue_token(user.user_id, user.username),
            token_type='bearer',
            user=user,
        )

    def _normalize_username(self, username: str) -> str:
        normalized = username.strip().lower()
        if len(normalized) < 3 or len(normalized) > 50:
            raise RegistrationError('用户名长度必须在 3 到 50 个字符之间。')
        return normalized

    def _validate_password(self, password: str) -> None:
        if len(password) < 8:
            raise RegistrationError('密码长度至少为 8 位。')
