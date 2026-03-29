from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from models.user import User
from services.auth_service import AuthenticationError

bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(request: Request):
    return request.app.state.container.auth_service


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = None,
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail='请先登录。')
    try:
        return get_auth_service(request).get_current_user(credentials.credentials)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
