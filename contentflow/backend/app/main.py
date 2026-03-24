import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db


logger = logging.getLogger("contentflow")


@asynccontextmanager
async def lifespan(app):
    try:
        from app.services.schedule_service import init_scheduler
        await init_scheduler()
    except Exception:
        pass
    yield


app = FastAPI(title="ContentFlow API", version="0.2.0", lifespan=lifespan)

from app.config import settings

allowed_origins = ["http://localhost:3000"]
if settings.frontend_url:
    allowed_origins.append(settings.frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000)
    logger.info(f"{request.method} {request.url.path} {response.status_code} {duration}ms")
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"code": "INTERNAL_ERROR", "message": "服务器内部错误"},
    )


@app.get("/api/health")
async def health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "error", "database": "disconnected"})


from app.routers import auth, user, content, brand_profile, schedule
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(content.router)
app.include_router(brand_profile.router)
app.include_router(schedule.router)
