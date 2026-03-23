from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.services.usage_service import get_usage

router = APIRouter(prefix="/api/user", tags=["user"])

@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return UserResponse(id=str(user.id), email=user.email, plan=user.plan)

@router.get("/usage")
async def get_user_usage(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_usage(db, user.id)
