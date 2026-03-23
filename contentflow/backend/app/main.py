from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ContentFlow API", version="0.1.0")

from app.config import settings

allowed_origins = ["http://localhost:3000"]
if settings.frontend_url:
    allowed_origins.append(settings.frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


from app.routers import auth, user, content
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(content.router)
