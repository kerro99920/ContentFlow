import uuid as _uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.auth_service import decode_token, get_user_by_id
from app.models.user import User

security = HTTPBearer()


def parse_uuid(value: str) -> _uuid.UUID:
    try:
        return _uuid.UUID(value)
    except ValueError:
        raise HTTPException(status_code=400, detail={"code": "INVALID_ID", "message": "无效的ID格式"})


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "INVALID_TOKEN", "message": "无效的令牌"})
    user = await get_user_by_id(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "USER_NOT_FOUND", "message": "用户不存在"})
    return user
