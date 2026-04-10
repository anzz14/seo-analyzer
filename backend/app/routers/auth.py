from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services import auth_service
from app.services.auth_service import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await auth_service.register_user(db, req.email, req.password)
    token = create_access_token(str(user.id), user.email)
    return TokenResponse(access_token=token, user_id=str(user.id), email=user.email)


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await auth_service.login_user(db, req.email, req.password)
    token = create_access_token(str(user.id), user.email)
    return TokenResponse(access_token=token, user_id=str(user.id), email=user.email)
