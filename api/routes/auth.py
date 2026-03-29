from fastapi import APIRouter, HTTPException, Request

from api.dependencies import get_auth_service
from schemas.auth import AuthCredentialsRequest, AuthResponse, UserResponse
from services.auth_service import AuthenticationError, RegistrationError

router = APIRouter(prefix='/api/auth', tags=['auth'])


@router.post('/register', response_model=AuthResponse)
async def register(request: Request, payload: AuthCredentialsRequest) -> AuthResponse:
    try:
        result = get_auth_service(request).register(payload.username, payload.password)
    except RegistrationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AuthResponse.from_domain(result)


@router.post('/login', response_model=AuthResponse)
async def login(request: Request, payload: AuthCredentialsRequest) -> AuthResponse:
    try:
        result = get_auth_service(request).login(payload.username, payload.password)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return AuthResponse.from_domain(result)


@router.get('/me', response_model=UserResponse)
async def me(request: Request) -> UserResponse:
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='请先登录。')
    token = auth_header.split(' ', 1)[1]
    try:
        user = get_auth_service(request).get_current_user(token)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return UserResponse.from_domain(user)
