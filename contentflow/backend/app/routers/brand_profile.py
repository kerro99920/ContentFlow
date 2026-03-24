from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.deps import get_current_user, parse_uuid
from app.models.user import User
from app.models.brand_profile import BrandProfile
from app.schemas.brand_profile import BrandProfileCreateRequest, BrandProfileResponse
from app.services.brand_service import generate_brand_system_prompt

router = APIRouter(prefix="/api/brand-profiles", tags=["brand-profiles"])

@router.post("", response_model=BrandProfileResponse, status_code=201)
async def create_brand_profile(req: BrandProfileCreateRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    system_prompt = await generate_brand_system_prompt(req.tone_description, req.industry_keywords)
    bp = BrandProfile(user_id=user.id, name=req.name, tone_description=req.tone_description, system_prompt=system_prompt, industry_keywords=req.industry_keywords)
    db.add(bp)
    await db.commit()
    await db.refresh(bp)
    return BrandProfileResponse(id=str(bp.id), name=bp.name, tone_description=bp.tone_description, system_prompt=bp.system_prompt, industry_keywords=bp.industry_keywords, created_at=bp.created_at.isoformat())

@router.get("", response_model=list[BrandProfileResponse])
async def list_brand_profiles(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(BrandProfile).where(BrandProfile.user_id == user.id))
    return [BrandProfileResponse(id=str(bp.id), name=bp.name, tone_description=bp.tone_description, system_prompt=bp.system_prompt, industry_keywords=bp.industry_keywords, created_at=bp.created_at.isoformat()) for bp in result.scalars()]

@router.delete("/{profile_id}", status_code=204)
async def delete_brand_profile(profile_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    bp = await db.get(BrandProfile, parse_uuid(profile_id))
    if not bp or bp.user_id != user.id:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "品牌档案不存在"})
    await db.delete(bp)
    await db.commit()
