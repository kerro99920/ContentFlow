from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
from app.services.auth_service import register, authenticate, create_token, decode_token, get_user_by_id

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register_user(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await register(db, req.email, req.password)
    if not user:
        raise HTTPException(status_code=400, detail={"code": "DUPLICATE_EMAIL", "message": "邮箱已注册"})
    return TokenResponse(
        access_token=create_token(str(user.id), "access"),
        refresh_token=create_token(str(user.id), "refresh"),
    )

@router.post("/login", response_model=TokenResponse)
async def login_user(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate(db, req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail={"code": "INVALID_CREDENTIALS", "message": "邮箱或密码错误"})
    return TokenResponse(
        access_token=create_token(str(user.id), "access"),
        refresh_token=create_token(str(user.id), "refresh"),
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail={"code": "INVALID_REFRESH_TOKEN", "message": "无效的刷新令牌"})
    user = await get_user_by_id(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail={"code": "USER_NOT_FOUND", "message": "用户不存在"})
    return TokenResponse(
        access_token=create_token(str(user.id), "access"),
        refresh_token=create_token(str(user.id), "refresh"),
    )
