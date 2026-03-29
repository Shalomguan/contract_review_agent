from pydantic import BaseModel, Field

from models.user import User
from services.auth_service import AuthResult


class AuthCredentialsRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)


class UserResponse(BaseModel):
    user_id: str
    username: str

    @classmethod
    def from_domain(cls, user: User) -> 'UserResponse':
        return cls(user_id=user.user_id, username=user.username)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

    @classmethod
    def from_domain(cls, result: AuthResult) -> 'AuthResponse':
        return cls(
            access_token=result.access_token,
            token_type=result.token_type,
            user=UserResponse.from_domain(result.user),
        )
