"""自动发布 API"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.deps import get_current_user, parse_uuid
from app.models.user import User
from app.models.content import Content
from app.services.publisher import publish_to_platform, login_to_platform, get_supported_platforms

router = APIRouter(prefix="/api/publish", tags=["publish"])


class PublishRequest(BaseModel):
    content_id: str
    platform: str


class LoginRequest(BaseModel):
    platform: str


@router.get("/platforms")
async def list_publish_platforms(user: User = Depends(get_current_user)):
    """获取支持自动发布的平台列表"""
    return get_supported_platforms()


@router.post("/login")
async def platform_login(
    req: LoginRequest,
    user: User = Depends(get_current_user),
):
    """启动浏览器让用户登录平台（需要在有桌面的环境运行）"""
    result = await login_to_platform(req.platform, str(user.id))
    if not result["success"]:
        raise HTTPException(status_code=400, detail={"code": "LOGIN_FAILED", "message": result["message"]})
    return result


@router.post("")
async def publish_content(
    req: PublishRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """发布内容到指定平台"""
    content_id = parse_uuid(req.content_id)
    content = await db.get(Content, content_id)
    if not content or content.user_id != user.id:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "内容不存在"})

    # 构建发布内容
    publish_data = {
        "title": content.title,
        "body": content.body,
        "tags": content.tags,
        "platform": content.platform,
    }
    if content.metadata_:
        publish_data.update(content.metadata_)

    result = await publish_to_platform(req.platform, publish_data, str(user.id))

    if result["success"]:
        content.status = "published"
        await db.commit()

    return result
