# ContentFlow Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a working SaaS MVP where users register via email, input text material, and get AI-generated Xiaohongshu content — with free tier quota enforcement.

**Architecture:** Monorepo with two apps: Next.js frontend (App Router) and FastAPI backend. Frontend calls backend REST API with JWT auth. AI generation runs as FastAPI BackgroundTasks. PostgreSQL stores all data, Redis caches sessions and rate limits.

**Tech Stack:** Next.js 14, Tailwind, shadcn/ui, FastAPI, SQLAlchemy 2.0, PostgreSQL, Redis (Upstash), Claude API, JWT, Vercel + Railway

**Spec:** `docs/superpowers/specs/2026-03-23-contentflow-design.md`

---

## File Structure

```
contentflow/
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app, CORS, lifespan
│   │   ├── config.py                 # Settings via pydantic-settings
│   │   ├── database.py               # async engine, session factory
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py               # User model
│   │   │   ├── content.py            # Content, GenerationTask models
│   │   │   │   └── usage.py              # UsageRecord model
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # Register/Login/Token schemas
│   │   │   ├── content.py            # Content request/response schemas
│   │   │   └── user.py               # User response schemas
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # POST register/login/refresh
│   │   │   ├── content.py            # Content CRUD + generate
│   │   │   └── user.py               # GET me/usage
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py       # Password hash, JWT, token logic
│   │   │   ├── content_service.py    # Content CRUD operations
│   │   │   ├── ai_service.py         # Claude/OpenAI API calls
│   │   │   ├── generation_service.py # Orchestrate generation + validation
│   │   │   └── usage_service.py      # Quota check and increment
│   │   ├── prompts/
│   │   │   ├── __init__.py
│   │   │   └── xiaohongshu.py        # XHS prompt templates (3 tones)
│   │   └── deps.py                   # Dependency injection (get_db, get_current_user)
│   └── tests/
│       ├── conftest.py               # Fixtures: test db, test client, test user
│       ├── test_auth.py
│       ├── test_content.py
│       ├── test_usage.py
│       └── test_generation.py
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── components.json               # shadcn/ui config
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx            # Root layout, fonts, metadata
│   │   │   ├── page.tsx              # Landing page
│   │   │   ├── (auth)/
│   │   │   │   ├── login/page.tsx
│   │   │   │   └── register/page.tsx
│   │   │   └── (dashboard)/
│   │   │       ├── layout.tsx        # Dashboard layout with sidebar
│   │   │       ├── generate/page.tsx # Content generation page
│   │   │       └── history/page.tsx  # Content history page
│   │   ├── components/
│   │   │   ├── ui/                   # shadcn/ui components
│   │   │   ├── landing/
│   │   │   │   ├── hero.tsx
│   │   │   │   ├── features.tsx
│   │   │   │   └── cta.tsx
│   │   │   ├── auth/
│   │   │   │   └── auth-form.tsx     # Shared login/register form
│   │   │   ├── dashboard/
│   │   │   │   ├── sidebar.tsx
│   │   │   │   └── header.tsx
│   │   │   └── content/
│   │   │       ├── generate-form.tsx # Material input + tone selector
│   │   │       ├── content-card.tsx  # Single content display card
│   │   │       └── content-list.tsx  # History list with pagination
│   │   └── lib/
│   │       ├── api.ts               # Fetch wrapper with auth headers
│   │       ├── auth.ts              # Token storage, refresh logic
│   │       └── types.ts             # TypeScript types matching backend schemas
│   └── public/
│       └── og-image.png
└── .github/
    └── workflows/
        ├── backend-ci.yml
        └── frontend-ci.yml
```

---

## Task 1: Backend Project Scaffolding

**Files:**
- Create: `contentflow/backend/pyproject.toml`
- Create: `contentflow/backend/app/__init__.py`
- Create: `contentflow/backend/app/main.py`
- Create: `contentflow/backend/app/config.py`
- Create: `contentflow/backend/app/database.py`

- [ ] **Step 1: Create project directory and pyproject.toml**

```toml
# contentflow/backend/pyproject.toml
[project]
name = "contentflow-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.30",
    "alembic>=1.14",
    "pydantic-settings>=2.7",
    "python-jose[cryptography]>=3.3",
    "passlib[bcrypt]>=1.7",
    "httpx>=0.28",
    "anthropic>=0.43",
    "redis>=5.2",
    "python-multipart>=0.0.18",
    "email-validator>=2.2",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[dependency-groups]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.25",
    "pytest-httpx>=0.35",
    "aiosqlite>=0.20",
]
```

- [ ] **Step 2: Create config.py with pydantic-settings**

```python
# contentflow/backend/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/contentflow"
    test_database_url: str = "sqlite+aiosqlite:///./test.db"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 120
    jwt_refresh_expire_days: int = 7

    anthropic_api_key: str = ""
    openai_api_key: str = ""

    free_monthly_quota: int = 10

    model_config = {"env_file": ".env"}

settings = Settings()
```

- [ ] **Step 3: Create database.py with async engine**

```python
# contentflow/backend/app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

engine = create_async_engine(settings.database_url)
async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
```

- [ ] **Step 4: Create main.py with FastAPI app**

```python
# contentflow/backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ContentFlow API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Create .env.example**

```bash
# contentflow/backend/.env.example
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/contentflow
TEST_DATABASE_URL=sqlite+aiosqlite:///./test.db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=change-me-in-production
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
```

- [ ] **Step 6: Install dependencies and verify server starts**

Run: `cd contentflow/backend && uv sync && uv run uvicorn app.main:app --reload --port 8000`
Expected: Server starts, `GET /api/health` returns `{"status": "ok"}`

- [ ] **Step 7: Commit**

```bash
git add contentflow/backend/
git commit -m "feat: scaffold backend with FastAPI + SQLAlchemy + config"
```

---

## Task 2: Database Models + Migrations

**Files:**
- Create: `contentflow/backend/app/models/user.py`
- Create: `contentflow/backend/app/models/content.py`
- Create: `contentflow/backend/app/models/usage.py`
- Create: `contentflow/backend/app/models/__init__.py`
- Create: `contentflow/backend/alembic.ini`
- Create: `contentflow/backend/alembic/env.py`

- [ ] **Step 1: Create User model**

```python
# contentflow/backend/app/models/user.py
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    plan: Mapped[str] = mapped_column(String(20), default="free")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    contents: Mapped[list["Content"]] = relationship(back_populates="user")
    usage_records: Mapped[list["UsageRecord"]] = relationship(back_populates="user")
```

- [ ] **Step 2: Create Content model**

```python
# contentflow/backend/app/models/content.py
import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Content(Base):
    __tablename__ = "contents"

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    source_material: Mapped[str] = mapped_column(Text)
    platform: Mapped[str] = mapped_column(String(50))  # xiaohongshu
    title: Mapped[str | None] = mapped_column(String(100))
    body: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[dict | None] = mapped_column(JSON)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON)
    brand_tone: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="contents")

class GenerationTask(Base):
    __tablename__ = "generation_tasks"

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/running/completed/failed
    source_material: Mapped[str] = mapped_column(Text)
    platform: Mapped[str] = mapped_column(String(50))
    brand_tone: Mapped[str] = mapped_column(String(50))
    content_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("contents.id"))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 3: Create UsageRecord model**

```python
# contentflow/backend/app/models/usage.py
import uuid
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class UsageRecord(Base):
    __tablename__ = "usage_records"

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    period: Mapped[str] = mapped_column(String(7), index=True)  # "2026-03"
    generation_count: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped["User"] = relationship(back_populates="usage_records")
```

- [ ] **Step 4: Create models __init__.py to re-export all models**

```python
# contentflow/backend/app/models/__init__.py
from app.models.user import User
from app.models.content import Content, GenerationTask
from app.models.usage import UsageRecord

__all__ = ["User", "Content", "GenerationTask", "UsageRecord"]
```

- [ ] **Step 5: Initialize Alembic and create async env.py**

Run:
```bash
cd contentflow/backend
uv run alembic init alembic
```

Replace `alembic/env.py` with async version:

```python
# contentflow/backend/alembic/env.py
import asyncio
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
from app.config import settings
from app.database import Base
from app.models import *  # noqa: F401, F403 -- register all models

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    context.configure(url=settings.database_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    connectable = create_async_engine(settings.database_url)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

Set `alembic.ini` `sqlalchemy.url` to empty (we use config.py instead):
```ini
sqlalchemy.url =
```

- [ ] **Step 6: Generate first migration**

Run:
```bash
uv run alembic revision --autogenerate -m "initial tables"
uv run alembic upgrade head
```

Expected: Migration file created under `alembic/versions/`, tables created in database.

- [ ] **Step 7: Commit**

```bash
git add contentflow/backend/app/models/ contentflow/backend/alembic*
git commit -m "feat: add database models and initial migration"
```

---

## Task 3: Auth System

**Files:**
- Create: `contentflow/backend/app/services/auth_service.py`
- Create: `contentflow/backend/app/schemas/auth.py`
- Create: `contentflow/backend/app/routers/auth.py`
- Create: `contentflow/backend/app/deps.py`
- Create: `contentflow/backend/tests/conftest.py`
- Create: `contentflow/backend/tests/test_auth.py`

- [ ] **Step 1: Write auth test cases**

```python
# contentflow/backend/tests/test_auth.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    resp = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "securepass123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data

@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {"email": "dup@example.com", "password": "pass123"}
    await client.post("/api/auth/register", json=payload)
    resp = await client.post("/api/auth/register", json=payload)
    assert resp.status_code == 400

@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post("/api/auth/register", json={
        "email": "login@example.com", "password": "pass123"
    })
    resp = await client.post("/api/auth/login", json={
        "email": "login@example.com", "password": "pass123"
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()

@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/auth/register", json={
        "email": "wrong@example.com", "password": "pass123"
    })
    resp = await client.post("/api/auth/login", json={
        "email": "wrong@example.com", "password": "wrongpass"
    })
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    reg = await client.post("/api/auth/register", json={
        "email": "refresh@example.com", "password": "pass123"
    })
    refresh_token = reg.json()["refresh_token"]
    resp = await client.post("/api/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()

@pytest.mark.asyncio
async def test_protected_route_no_token(client: AsyncClient):
    resp = await client.get("/api/user/me")
    assert resp.status_code == 401
```

- [ ] **Step 2: Create test conftest.py**

```python
# contentflow/backend/tests/conftest.py
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.main import app
from app.database import Base, get_db
from app.config import settings
from app.models.user import User
from app.services.auth_service import hash_password, create_token

test_engine = create_async_engine(settings.test_database_url)
test_session = async_sessionmaker(test_engine, expire_on_commit=False)

async def override_get_db():
    async with test_session() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.fixture
async def db_session():
    async with test_session() as session:
        yield session

@pytest.fixture
async def test_user(db_session):
    user = User(email="fixture@test.com", hashed_password=hash_password("testpass"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def authed_client(test_user):
    token = create_token(str(test_user.id), "access")
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as c:
        yield c
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd contentflow/backend && uv run pytest tests/test_auth.py -v`
Expected: All tests FAIL (routes don't exist yet)

- [ ] **Step 4: Create auth schemas**

```python
# contentflow/backend/app/schemas/auth.py
from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str
```

- [ ] **Step 5: Create auth service**

```python
# contentflow/backend/app/services/auth_service.py
import uuid
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(user_id: str, token_type: str = "access") -> str:
    if token_type == "access":
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_expire_minutes)
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_expire_days)
    payload = {"sub": user_id, "type": token_type, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None

async def register(db: AsyncSession, email: str, password: str) -> User | None:
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        return None
    user = User(email=email, hashed_password=hash_password(password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def authenticate(db: AsyncSession, email: str, password: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    return result.scalar_one_or_none()
```

- [ ] **Step 6: Create deps.py with get_current_user**

```python
# contentflow/backend/app/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.auth_service import decode_token, get_user_by_id
from app.models.user import User

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = await get_user_by_id(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
```

- [ ] **Step 7: Create auth router**

```python
# contentflow/backend/app/routers/auth.py
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
        raise HTTPException(status_code=400, detail="Email already registered")
    return TokenResponse(
        access_token=create_token(str(user.id), "access"),
        refresh_token=create_token(str(user.id), "refresh"),
    )

@router.post("/login", response_model=TokenResponse)
async def login_user(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate(db, req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(
        access_token=create_token(str(user.id), "access"),
        refresh_token=create_token(str(user.id), "refresh"),
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = await get_user_by_id(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return TokenResponse(
        access_token=create_token(str(user.id), "access"),
        refresh_token=create_token(str(user.id), "refresh"),
    )
```

- [ ] **Step 8: Create user router (for /api/user/me)**

```python
# contentflow/backend/app/routers/user.py
from fastapi import APIRouter, Depends
from app.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter(prefix="/api/user", tags=["user"])

@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return UserResponse(id=str(user.id), email=user.email, plan=user.plan)
```

```python
# contentflow/backend/app/schemas/user.py
from pydantic import BaseModel

class UserResponse(BaseModel):
    id: str
    email: str
    plan: str
```

- [ ] **Step 9: Register routers in main.py**

Update `contentflow/backend/app/main.py` to include:
```python
from app.routers import auth, user
app.include_router(auth.router)
app.include_router(user.router)
```

- [ ] **Step 10: Run tests to verify all pass**

Run: `cd contentflow/backend && uv run pytest tests/test_auth.py -v`
Expected: All 6 tests PASS

- [ ] **Step 11: Commit**

```bash
git add contentflow/backend/
git commit -m "feat: add email auth system with JWT (register/login/refresh)"
```

---

## Task 4: Usage Quota Service

**Files:**
- Create: `contentflow/backend/app/services/usage_service.py`
- Create: `contentflow/backend/tests/test_usage.py`

- [ ] **Step 1: Write usage service tests**

```python
# contentflow/backend/tests/test_usage.py
import pytest
from app.services.usage_service import check_quota, increment_usage, get_usage

@pytest.mark.asyncio
async def test_new_user_has_quota(db_session, test_user):
    has_quota = await check_quota(db_session, test_user.id)
    assert has_quota is True

@pytest.mark.asyncio
async def test_increment_and_check(db_session, test_user):
    for _ in range(10):
        await increment_usage(db_session, test_user.id)
    has_quota = await check_quota(db_session, test_user.id)
    assert has_quota is False

@pytest.mark.asyncio
async def test_get_usage_returns_count(db_session, test_user):
    await increment_usage(db_session, test_user.id)
    await increment_usage(db_session, test_user.id)
    usage = await get_usage(db_session, test_user.id)
    assert usage["generation_count"] == 2
    assert usage["quota"] == 10
```

Add `db_session` and `test_user` fixtures to `conftest.py`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd contentflow/backend && uv run pytest tests/test_usage.py -v`
Expected: FAIL (module doesn't exist)

- [ ] **Step 3: Implement usage service**

```python
# contentflow/backend/app/services/usage_service.py
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.usage import UsageRecord
from app.config import settings
import uuid

def _current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")

async def _get_or_create_record(db: AsyncSession, user_id: uuid.UUID) -> UsageRecord:
    period = _current_period()
    result = await db.execute(
        select(UsageRecord).where(
            UsageRecord.user_id == user_id,
            UsageRecord.period == period,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        record = UsageRecord(user_id=user_id, period=period, generation_count=0)
        db.add(record)
        await db.flush()
    return record

async def check_quota(db: AsyncSession, user_id: uuid.UUID) -> bool:
    record = await _get_or_create_record(db, user_id)
    return record.generation_count < settings.free_monthly_quota

async def increment_usage(db: AsyncSession, user_id: uuid.UUID) -> None:
    record = await _get_or_create_record(db, user_id)
    record.generation_count += 1
    await db.commit()

async def get_usage(db: AsyncSession, user_id: uuid.UUID) -> dict:
    record = await _get_or_create_record(db, user_id)
    return {
        "period": record.period,
        "generation_count": record.generation_count,
        "quota": settings.free_monthly_quota,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd contentflow/backend && uv run pytest tests/test_usage.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add contentflow/backend/app/services/usage_service.py contentflow/backend/tests/test_usage.py
git commit -m "feat: add usage quota tracking service"
```

---

## Task 5: AI Content Generation Service

**Files:**
- Create: `contentflow/backend/app/prompts/xiaohongshu.py`
- Create: `contentflow/backend/app/services/ai_service.py`
- Create: `contentflow/backend/app/services/generation_service.py`
- Create: `contentflow/backend/tests/test_generation.py`

- [ ] **Step 1: Create Xiaohongshu prompt templates**

```python
# contentflow/backend/app/prompts/xiaohongshu.py

PLATFORM_RULES = """小红书平台规范：
- 标题：≤20字，吸引眼球，可用 emoji
- 正文：≤1000字，口语化，分段清晰，适当使用 emoji
- 话题标签：5-10个，包含热门标签和长尾标签
- 封面文案建议：1句话，适合做图片封面文字"""

TONE_TEMPLATES = {
    "professional": "专业严谨风格：用数据说话，引用权威来源，语气沉稳可信，适合知识科普和行业分析。",
    "casual": "轻松活泼风格：像朋友聊天一样，用口语化表达，多用语气词和 emoji，适合日常分享。",
    "seeding": "种草安利风格：真实使用体验，突出产品亮点和使用场景，有感染力，适合好物推荐。",
}

def build_system_prompt(tone: str) -> str:
    tone_desc = TONE_TEMPLATES.get(tone, TONE_TEMPLATES["casual"])
    return f"""你是一位专业的小红书内容创作专家。
{tone_desc}
{PLATFORM_RULES}

你的输出必须严格遵循以下 JSON 格式：
{{
  "title": "标题（≤20字）",
  "body": "正文内容（≤1000字）",
  "tags": ["标签1", "标签2", ...],
  "cover_text": "封面文案建议"
}}

只输出 JSON，不要输出其他内容。"""

def build_user_prompt(source_material: str) -> str:
    return f"请基于以下素材，生成一篇小红书笔记：\n\n{source_material}"
```

- [ ] **Step 2: Create AI service (Claude API wrapper)**

```python
# contentflow/backend/app/services/ai_service.py
import json
import anthropic
from app.config import settings

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

async def generate_content(system_prompt: str, user_prompt: str) -> dict:
    """调用 Claude API 生成内容，返回解析后的 JSON dict。"""
    message = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    raw_text = message.content[0].text.strip()
    # 去除可能的 markdown code fence
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(raw_text)
```

- [ ] **Step 3: Create generation service (orchestrator)**

```python
# contentflow/backend/app/services/generation_service.py
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.content import Content, GenerationTask
from app.services.ai_service import generate_content
from app.services.usage_service import check_quota, increment_usage
from app.prompts.xiaohongshu import build_system_prompt, build_user_prompt

VALIDATORS = {
    "xiaohongshu": lambda d: (
        len(d.get("title", "")) <= 20
        and len(d.get("body", "")) <= 1000
        and isinstance(d.get("tags"), list)
    ),
}

async def run_generation(
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    source_material: str,
    platform: str,
    brand_tone: str,
) -> None:
    """后台任务：执行 AI 生成并保存结果。使用独立 DB session。"""
    from app.database import async_session
    async with async_session() as db:
        await _do_generation(db, task_id, user_id, source_material, platform, brand_tone)

async def _do_generation(
    db: AsyncSession,
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    source_material: str,
    platform: str,
    brand_tone: str,
) -> None:
    # 更新任务状态
    task = await db.get(GenerationTask, task_id)
    task.status = "running"
    await db.commit()

    try:
        system_prompt = build_system_prompt(brand_tone)
        user_prompt = build_user_prompt(source_material)

        # 最多重试 2 次
        result = None
        for attempt in range(3):
            result = await generate_content(system_prompt, user_prompt)
            validator = VALIDATORS.get(platform, lambda _: True)
            if validator(result):
                break
        else:
            task.status = "failed"
            task.error_message = "内容校验未通过，请重试"
            await db.commit()
            return

        # 保存生成的内容
        content = Content(
            user_id=user_id,
            source_material=source_material,
            platform=platform,
            title=result.get("title"),
            body=result.get("body"),
            tags=result.get("tags"),
            metadata_={"cover_text": result.get("cover_text")},
            brand_tone=brand_tone,
            status="draft",
        )
        db.add(content)
        await db.flush()

        task.status = "completed"
        task.content_id = content.id
        await increment_usage(db, user_id)
        await db.commit()

    except Exception as e:
        task.status = "failed"
        task.error_message = str(e)
        await db.commit()
```

- [ ] **Step 4: Write test for generation service (mock AI)**

```python
# contentflow/backend/tests/test_generation.py
import pytest
from unittest.mock import AsyncMock, patch
from app.services.generation_service import run_generation
from app.models.content import GenerationTask

MOCK_AI_RESPONSE = {
    "title": "测试标题",
    "body": "测试正文内容",
    "tags": ["测试", "AI"],
    "cover_text": "封面文案",
}

@pytest.mark.asyncio
@patch("app.services.generation_service.generate_content", new_callable=AsyncMock)
@patch("app.services.generation_service.async_session")
async def test_generation_creates_content(mock_session_factory, mock_ai, db_session, test_user):
    mock_ai.return_value = MOCK_AI_RESPONSE
    # 让 run_generation 使用测试 db session
    from tests.conftest import test_session
    mock_session_factory.return_value = test_session()

    task = GenerationTask(
        user_id=test_user.id,
        source_material="测试素材",
        platform="xiaohongshu",
        brand_tone="casual",
    )
    db_session.add(task)
    await db_session.commit()

    await run_generation(
        task.id, test_user.id,
        "测试素材", "xiaohongshu", "casual"
    )

    await db_session.refresh(task)
    assert task.status == "completed"
    assert task.content_id is not None
```

- [ ] **Step 5: Run tests**

Run: `cd contentflow/backend && uv run pytest tests/test_generation.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add contentflow/backend/app/prompts/ contentflow/backend/app/services/ contentflow/backend/tests/
git commit -m "feat: add AI content generation with XHS prompts and validation"
```

---

## Task 6: Content API Routes

**Files:**
- Create: `contentflow/backend/app/schemas/content.py`
- Create: `contentflow/backend/app/routers/content.py`
- Create: `contentflow/backend/tests/test_content.py`

- [ ] **Step 1: Write content API tests**

```python
# contentflow/backend/tests/test_content.py
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

MOCK_RESULT = {
    "title": "测试", "body": "内容", "tags": ["tag"], "cover_text": "封面"
}

@pytest.mark.asyncio
async def test_generate_content(authed_client: AsyncClient):
    with patch("app.routers.content.run_generation", new_callable=AsyncMock):
        resp = await authed_client.post("/api/content/generate", json={
            "source_material": "测试素材",
            "platform": "xiaohongshu",
            "brand_tone": "casual",
        })
    assert resp.status_code == 202
    assert "task_id" in resp.json()

@pytest.mark.asyncio
async def test_generate_exceeds_quota(authed_client: AsyncClient, db_session, test_user):
    # 手动设置额度用尽
    from app.services.usage_service import increment_usage
    for _ in range(10):
        await increment_usage(db_session, test_user.id)

    resp = await authed_client.post("/api/content/generate", json={
        "source_material": "测试", "platform": "xiaohongshu", "brand_tone": "casual",
    })
    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "QUOTA_EXCEEDED"

@pytest.mark.asyncio
async def test_list_content(authed_client: AsyncClient):
    resp = await authed_client.get("/api/content")
    assert resp.status_code == 200
    assert "items" in resp.json()

@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    resp = await client.get("/api/content")
    assert resp.status_code == 401
```

Add `authed_client` fixture to conftest.py (a client with valid JWT header).

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd contentflow/backend && uv run pytest tests/test_content.py -v`
Expected: FAIL

- [ ] **Step 3: Create content schemas**

```python
# contentflow/backend/app/schemas/content.py
from pydantic import BaseModel

class GenerateRequest(BaseModel):
    source_material: str
    platform: str = "xiaohongshu"
    brand_tone: str = "casual"

class GenerateResponse(BaseModel):
    task_id: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    content_id: str | None = None
    error_message: str | None = None

class ContentResponse(BaseModel):
    id: str
    platform: str
    title: str | None
    body: str | None
    tags: list | None
    metadata: dict | None
    brand_tone: str | None
    status: str
    created_at: str

class ContentListResponse(BaseModel):
    items: list[ContentResponse]
    total: int
    page: int
    page_size: int
```

- [ ] **Step 4: Create content router**

```python
# contentflow/backend/app/routers/content.py
import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.content import Content, GenerationTask
from app.schemas.content import (
    GenerateRequest, GenerateResponse, TaskStatusResponse,
    ContentResponse, ContentListResponse,
)
from app.services.usage_service import check_quota
from app.services.generation_service import run_generation

router = APIRouter(prefix="/api/content", tags=["content"])

@router.post("/generate", response_model=GenerateResponse, status_code=202)
async def generate(
    req: GenerateRequest,
    bg: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not await check_quota(db, user.id):
        raise HTTPException(
            status_code=403,
            detail={"code": "QUOTA_EXCEEDED", "message": "本月免费额度已用完"},
        )

    task = GenerationTask(
        user_id=user.id,
        source_material=req.source_material,
        platform=req.platform,
        brand_tone=req.brand_tone,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    bg.add_task(run_generation, task.id, user.id, req.source_material, req.platform, req.brand_tone)

    return GenerateResponse(task_id=str(task.id))

@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = await db.get(GenerationTask, uuid.UUID(task_id))
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskStatusResponse(
        task_id=str(task.id),
        status=task.status,
        content_id=str(task.content_id) if task.content_id else None,
        error_message=task.error_message,
    )

@router.get("", response_model=ContentListResponse)
async def list_content(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    offset = (page - 1) * page_size
    query = select(Content).where(Content.user_id == user.id).order_by(Content.created_at.desc())
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()
    result = await db.execute(query.offset(offset).limit(page_size))
    items = [
        ContentResponse(
            id=str(c.id), platform=c.platform, title=c.title, body=c.body,
            tags=c.tags, metadata=c.metadata_, brand_tone=c.brand_tone,
            status=c.status, created_at=c.created_at.isoformat(),
        )
        for c in result.scalars()
    ]
    return ContentListResponse(items=items, total=total, page=page, page_size=page_size)

@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = await db.get(Content, uuid.UUID(content_id))
    if not content or content.user_id != user.id:
        raise HTTPException(status_code=404, detail="Content not found")
    return ContentResponse(
        id=str(content.id), platform=content.platform, title=content.title,
        body=content.body, tags=content.tags, metadata=content.metadata_,
        brand_tone=content.brand_tone, status=content.status,
        created_at=content.created_at.isoformat(),
    )

@router.delete("/{content_id}", status_code=204)
async def delete_content(
    content_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = await db.get(Content, uuid.UUID(content_id))
    if not content or content.user_id != user.id:
        raise HTTPException(status_code=404, detail="Content not found")
    await db.delete(content)
    await db.commit()
```

- [ ] **Step 5: Register content router in main.py**

```python
from app.routers import auth, user, content
app.include_router(content.router)
```

- [ ] **Step 6: Run all backend tests**

Run: `cd contentflow/backend && uv run pytest -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add contentflow/backend/
git commit -m "feat: add content generation API with quota enforcement"
```

---

## Task 7: Frontend Scaffolding

**Files:**
- Create: `contentflow/frontend/` (Next.js project)
- Create: `contentflow/frontend/src/lib/api.ts`
- Create: `contentflow/frontend/src/lib/auth.ts`
- Create: `contentflow/frontend/src/lib/types.ts`

- [ ] **Step 1: Create Next.js project**

Run:
```bash
cd contentflow
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --no-import-alias
```

- [ ] **Step 2: Install shadcn/ui**

Run:
```bash
cd contentflow/frontend
npx shadcn@latest init
npx shadcn@latest add button input label card textarea badge tabs select toast
```

- [ ] **Step 3: Create API client**

```typescript
// contentflow/frontend/src/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("access_token");
  }

  async fetch<T>(path: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    });

    if (res.status === 401) {
      const refreshed = await this.refreshToken();
      if (refreshed) {
        return this.fetch(path, options);
      }
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      window.location.href = "/login";
      throw new Error("Unauthorized");
    }

    if (!res.ok) {
      const error = await res.json().catch(() => ({}));
      throw new Error(error?.detail?.error?.message || error?.detail || "Request failed");
    }

    if (res.status === 204) return {} as T;
    return res.json();
  }

  private async refreshToken(): Promise<boolean> {
    const refreshToken = localStorage.getItem("refresh_token");
    if (!refreshToken) return false;
    try {
      const res = await fetch(`${API_BASE}/api/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!res.ok) return false;
      const data = await res.json();
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      return true;
    } catch {
      return false;
    }
  }
}

export const api = new ApiClient();
```

- [ ] **Step 4: Create auth helpers**

```typescript
// contentflow/frontend/src/lib/auth.ts
import { api } from "./api";

interface TokenResponse {
  access_token: string;
  refresh_token: string;
}

export async function register(email: string, password: string): Promise<void> {
  const data = await api.fetch<TokenResponse>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
}

export async function login(email: string, password: string): Promise<void> {
  const data = await api.fetch<TokenResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
}

export function logout(): void {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  window.location.href = "/login";
}

export function isLoggedIn(): boolean {
  return typeof window !== "undefined" && !!localStorage.getItem("access_token");
}
```

- [ ] **Step 5: Create root layout**

```tsx
// contentflow/frontend/src/app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ContentFlow - 一个素材进，全平台内容出",
  description: "AI 驱动的多平台内容自动化工具",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
```

Note: `create-next-app` auto-generates this file, but replace its content with the above.

- [ ] **Step 6: Create TypeScript types**

```typescript
// contentflow/frontend/src/lib/types.ts
export interface ContentItem {
  id: string;
  platform: string;
  title: string | null;
  body: string | null;
  tags: string[] | null;
  metadata: Record<string, unknown> | null;
  brand_tone: string | null;
  status: string;
  created_at: string;
}

export interface ContentListResponse {
  items: ContentItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface GenerateResponse {
  task_id: string;
}

export interface TaskStatus {
  task_id: string;
  status: "pending" | "running" | "completed" | "failed";
  content_id: string | null;
  error_message: string | null;
}

export interface UserInfo {
  id: string;
  email: string;
  plan: string;
}

export interface UsageInfo {
  period: string;
  generation_count: number;
  quota: number;
}
```

- [ ] **Step 6: Verify dev server starts**

Run: `cd contentflow/frontend && npm run dev`
Expected: Next.js dev server starts on localhost:3000

- [ ] **Step 7: Commit**

```bash
git add contentflow/frontend/
git commit -m "feat: scaffold frontend with Next.js, shadcn/ui, API client"
```

---

## Task 8: Landing Page

**Files:**
- Create: `contentflow/frontend/src/app/page.tsx`
- Create: `contentflow/frontend/src/components/landing/hero.tsx`
- Create: `contentflow/frontend/src/components/landing/features.tsx`
- Create: `contentflow/frontend/src/components/landing/cta.tsx`

- [ ] **Step 1: Create Hero component**

```tsx
// contentflow/frontend/src/components/landing/hero.tsx
import Link from "next/link";
import { Button } from "@/components/ui/button";

export function Hero() {
  return (
    <section className="flex flex-col items-center justify-center gap-6 py-24 text-center">
      <h1 className="text-5xl font-bold tracking-tight">
        一个素材进，全平台内容出
      </h1>
      <p className="max-w-2xl text-xl text-muted-foreground">
        输入一段文字，AI 自动生成适配小红书、抖音、公众号、博客的专业内容。
        告别重复劳动，专注创作本身。
      </p>
      <div className="flex gap-4">
        <Link href="/register">
          <Button size="lg">免费开始</Button>
        </Link>
        <Link href="#features">
          <Button size="lg" variant="outline">了解更多</Button>
        </Link>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Create Features component**

```tsx
// contentflow/frontend/src/components/landing/features.tsx
const features = [
  {
    title: "多平台适配",
    description: "一次输入，自动生成适配小红书、抖音等平台规范的内容",
  },
  {
    title: "品牌调性一致",
    description: "预设多种风格模板，确保每篇内容都符合你的品牌人设",
  },
  {
    title: "AI 驱动",
    description: "基于顶级 AI 模型，生成高质量、高完播率的专业内容",
  },
];

export function Features() {
  return (
    <section id="features" className="py-20">
      <h2 className="mb-12 text-center text-3xl font-bold">核心能力</h2>
      <div className="grid gap-8 md:grid-cols-3">
        {features.map((f) => (
          <div key={f.title} className="rounded-lg border p-6">
            <h3 className="mb-2 text-xl font-semibold">{f.title}</h3>
            <p className="text-muted-foreground">{f.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
```

- [ ] **Step 3: Create CTA component**

```tsx
// contentflow/frontend/src/components/landing/cta.tsx
import Link from "next/link";
import { Button } from "@/components/ui/button";

export function CTA() {
  return (
    <section className="py-20 text-center">
      <h2 className="mb-4 text-3xl font-bold">每月 10 次免费生成</h2>
      <p className="mb-8 text-muted-foreground">无需信用卡，立即体验 AI 内容生成</p>
      <Link href="/register">
        <Button size="lg">免费注册</Button>
      </Link>
    </section>
  );
}
```

- [ ] **Step 4: Assemble landing page**

```tsx
// contentflow/frontend/src/app/page.tsx
import { Hero } from "@/components/landing/hero";
import { Features } from "@/components/landing/features";
import { CTA } from "@/components/landing/cta";

export default function Home() {
  return (
    <main className="mx-auto max-w-5xl px-4">
      <Hero />
      <Features />
      <CTA />
    </main>
  );
}
```

- [ ] **Step 5: Verify page renders**

Run: `cd contentflow/frontend && npm run dev`, open `http://localhost:3000`
Expected: Landing page renders with hero, features, CTA sections

- [ ] **Step 6: Commit**

```bash
git add contentflow/frontend/src/
git commit -m "feat: add landing page with hero, features, CTA"
```

---

## Task 9: Auth Pages (Register/Login)

**Files:**
- Create: `contentflow/frontend/src/components/auth/auth-form.tsx`
- Create: `contentflow/frontend/src/app/(auth)/login/page.tsx`
- Create: `contentflow/frontend/src/app/(auth)/register/page.tsx`

- [ ] **Step 1: Create shared auth form component**

```tsx
// contentflow/frontend/src/components/auth/auth-form.tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { login, register } from "@/lib/auth";

interface AuthFormProps {
  mode: "login" | "register";
}

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "register") {
        await register(email, password);
      } else {
        await login(email, password);
      }
      router.push("/generate");
    } catch (err) {
      setError(err instanceof Error ? err.message : "操作失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="mx-auto mt-20 w-full max-w-md">
      <CardHeader>
        <CardTitle>{mode === "login" ? "登录" : "注册"}</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="email">邮箱</Label>
            <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div>
            <Label htmlFor="password">密码</Label>
            <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} />
          </div>
          {error && <p className="text-sm text-red-500">{error}</p>}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "处理中..." : mode === "login" ? "登录" : "注册"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 2: Create login and register pages**

```tsx
// contentflow/frontend/src/app/(auth)/login/page.tsx
import { AuthForm } from "@/components/auth/auth-form";
export default function LoginPage() {
  return <AuthForm mode="login" />;
}
```

```tsx
// contentflow/frontend/src/app/(auth)/register/page.tsx
import { AuthForm } from "@/components/auth/auth-form";
export default function RegisterPage() {
  return <AuthForm mode="register" />;
}
```

- [ ] **Step 3: Verify pages render and form works**

Run: Open `http://localhost:3000/login` and `http://localhost:3000/register`
Expected: Forms render correctly, submit sends API request

- [ ] **Step 4: Commit**

```bash
git add contentflow/frontend/src/
git commit -m "feat: add login and register pages"
```

---

## Task 10: Dashboard — Content Generation Page

**Files:**
- Create: `contentflow/frontend/src/app/(dashboard)/layout.tsx`
- Create: `contentflow/frontend/src/app/(dashboard)/generate/page.tsx`
- Create: `contentflow/frontend/src/components/dashboard/sidebar.tsx`
- Create: `contentflow/frontend/src/components/content/generate-form.tsx`
- Create: `contentflow/frontend/src/components/content/content-card.tsx`

- [ ] **Step 1: Create dashboard layout with sidebar**

```tsx
// contentflow/frontend/src/components/dashboard/sidebar.tsx
"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { logout } from "@/lib/auth";

const navItems = [
  { href: "/generate", label: "内容生成" },
  { href: "/history", label: "历史记录" },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="flex h-screen w-56 flex-col border-r p-4">
      <h2 className="mb-6 text-lg font-bold">ContentFlow</h2>
      <nav className="flex flex-1 flex-col gap-1">
        {navItems.map((item) => (
          <Link key={item.href} href={item.href}>
            <Button variant={pathname === item.href ? "secondary" : "ghost"} className="w-full justify-start">
              {item.label}
            </Button>
          </Link>
        ))}
      </nav>
      <Button variant="outline" onClick={logout}>退出登录</Button>
    </aside>
  );
}
```

```tsx
// contentflow/frontend/src/app/(dashboard)/layout.tsx
import { Sidebar } from "@/components/dashboard/sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8">{children}</main>
    </div>
  );
}
```

- [ ] **Step 2: Create generate form component**

```tsx
// contentflow/frontend/src/components/content/generate-form.tsx
"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import type { GenerateResponse, TaskStatus, ContentItem } from "@/lib/types";

const tones = [
  { value: "professional", label: "专业严谨" },
  { value: "casual", label: "轻松活泼" },
  { value: "seeding", label: "种草安利" },
];

interface Props {
  onGenerated: (content: ContentItem) => void;
}

export function GenerateForm({ onGenerated }: Props) {
  const [material, setMaterial] = useState("");
  const [tone, setTone] = useState("casual");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (!material.trim()) return;
    setLoading(true);
    setError("");

    try {
      const { task_id } = await api.fetch<GenerateResponse>("/api/content/generate", {
        method: "POST",
        body: JSON.stringify({
          source_material: material,
          platform: "xiaohongshu",
          brand_tone: tone,
        }),
      });

      // 轮询任务状态
      let status: TaskStatus;
      do {
        await new Promise((r) => setTimeout(r, 1500));
        status = await api.fetch<TaskStatus>(`/api/content/tasks/${task_id}`);
      } while (status.status === "pending" || status.status === "running");

      if (status.status === "completed" && status.content_id) {
        const content = await api.fetch<ContentItem>(`/api/content/${status.content_id}`);
        onGenerated(content);
        setMaterial("");
      } else {
        setError(status.error_message || "生成失败，请重试");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "请求失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <Label>素材内容</Label>
        <Textarea
          value={material}
          onChange={(e) => setMaterial(e.target.value)}
          placeholder="输入你的素材：产品描述、灵感、主题..."
          rows={6}
        />
      </div>
      <div>
        <Label>品牌调性</Label>
        <Select value={tone} onValueChange={setTone}>
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            {tones.map((t) => (
              <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      {error && <p className="text-sm text-red-500">{error}</p>}
      <Button onClick={handleGenerate} disabled={loading || !material.trim()}>
        {loading ? "AI 生成中..." : "生成小红书内容"}
      </Button>
    </div>
  );
}
```

- [ ] **Step 3: Create content display card**

```tsx
// contentflow/frontend/src/components/content/content-card.tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ContentItem } from "@/lib/types";

export function ContentCard({ content }: { content: ContentItem }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">{content.title || "无标题"}</CardTitle>
          <Badge variant="secondary">{content.platform}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="whitespace-pre-wrap text-sm">{content.body}</p>
        {content.tags && (
          <div className="flex flex-wrap gap-1">
            {content.tags.map((tag) => (
              <Badge key={tag} variant="outline">#{tag}</Badge>
            ))}
          </div>
        )}
        {content.metadata?.cover_text && (
          <p className="text-sm text-muted-foreground">封面建议：{String(content.metadata.cover_text)}</p>
        )}
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 4: Create generate page**

```tsx
// contentflow/frontend/src/app/(dashboard)/generate/page.tsx
"use client";
import { useState } from "react";
import { GenerateForm } from "@/components/content/generate-form";
import { ContentCard } from "@/components/content/content-card";
import type { ContentItem } from "@/lib/types";

export default function GeneratePage() {
  const [result, setResult] = useState<ContentItem | null>(null);

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-6 text-2xl font-bold">生成小红书内容</h1>
      <GenerateForm onGenerated={setResult} />
      {result && (
        <div className="mt-8">
          <h2 className="mb-4 text-lg font-semibold">生成结果</h2>
          <ContentCard content={result} />
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Verify full flow works**

Run: Start both backend and frontend, register a user, enter material, click generate.
Expected: Content generated and displayed in card.

- [ ] **Step 6: Commit**

```bash
git add contentflow/frontend/src/
git commit -m "feat: add dashboard with content generation page"
```

---

## Task 11: Dashboard — Content History Page

**Files:**
- Create: `contentflow/frontend/src/app/(dashboard)/history/page.tsx`
- Create: `contentflow/frontend/src/components/content/content-list.tsx`

- [ ] **Step 1: Create content list component**

```tsx
// contentflow/frontend/src/components/content/content-list.tsx
"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ContentCard } from "./content-card";
import { Button } from "@/components/ui/button";
import type { ContentItem, ContentListResponse } from "@/lib/types";

export function ContentList() {
  const [items, setItems] = useState<ContentItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const fetchPage = async (p: number) => {
    setLoading(true);
    try {
      const data = await api.fetch<ContentListResponse>(`/api/content?page=${p}&page_size=10`);
      setItems(data.items);
      setTotal(data.total);
      setPage(p);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchPage(1); }, []);

  const totalPages = Math.ceil(total / 10);

  if (loading) return <p className="text-muted-foreground">加载中...</p>;
  if (items.length === 0) return <p className="text-muted-foreground">暂无内容，去生成第一篇吧</p>;

  return (
    <div className="space-y-4">
      {items.map((item) => (
        <ContentCard key={item.id} content={item} />
      ))}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <Button variant="outline" disabled={page <= 1} onClick={() => fetchPage(page - 1)}>上一页</Button>
          <span className="flex items-center text-sm text-muted-foreground">{page} / {totalPages}</span>
          <Button variant="outline" disabled={page >= totalPages} onClick={() => fetchPage(page + 1)}>下一页</Button>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Create history page**

```tsx
// contentflow/frontend/src/app/(dashboard)/history/page.tsx
import { ContentList } from "@/components/content/content-list";

export default function HistoryPage() {
  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-6 text-2xl font-bold">历史记录</h1>
      <ContentList />
    </div>
  );
}
```

- [ ] **Step 3: Verify page renders with pagination**

Run: Open `http://localhost:3000/history`
Expected: Displays content list with pagination (or empty state if no content)

- [ ] **Step 4: Commit**

```bash
git add contentflow/frontend/src/
git commit -m "feat: add content history page with pagination"
```

---

## Task 12: User Usage Display + Route Protection

**Files:**
- Modify: `contentflow/frontend/src/components/dashboard/sidebar.tsx`
- Create: `contentflow/frontend/src/components/dashboard/usage-badge.tsx`

- [ ] **Step 1: Create usage badge component**

```tsx
// contentflow/frontend/src/components/dashboard/usage-badge.tsx
"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { UsageInfo } from "@/lib/types";

export function UsageBadge() {
  const [usage, setUsage] = useState<UsageInfo | null>(null);

  useEffect(() => {
    api.fetch<UsageInfo>("/api/user/usage").then(setUsage).catch(() => {});
  }, []);

  if (!usage) return null;

  return (
    <div className="mb-4 rounded-lg border p-3 text-sm">
      <p className="text-muted-foreground">本月用量</p>
      <p className="text-lg font-semibold">{usage.generation_count} / {usage.quota}</p>
    </div>
  );
}
```

- [ ] **Step 2: Add UsageBadge to sidebar**

Update sidebar to include `<UsageBadge />` above the logout button.

- [ ] **Step 3: Add /api/user/usage endpoint to backend**

```python
# Add to contentflow/backend/app/routers/user.py
from app.services.usage_service import get_usage
from app.database import get_db

@router.get("/usage")
async def get_user_usage(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_usage(db, user.id)
```

- [ ] **Step 4: Verify usage displays in sidebar**

Expected: Sidebar shows "本月用量 0 / 10", increments after generation.

- [ ] **Step 5: Commit**

```bash
git add contentflow/
git commit -m "feat: add usage quota display in dashboard sidebar"
```

---

## Task 13: CI/CD Setup

**Files:**
- Create: `contentflow/.github/workflows/backend-ci.yml`
- Create: `contentflow/.github/workflows/frontend-ci.yml`

- [ ] **Step 1: Create backend CI workflow**

```yaml
# contentflow/.github/workflows/backend-ci.yml
name: Backend CI
on:
  push:
    paths: ["backend/**"]
  pull_request:
    paths: ["backend/**"]

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync
      - run: uv run pytest -v
```

- [ ] **Step 2: Create frontend CI workflow**

```yaml
# contentflow/.github/workflows/frontend-ci.yml
name: Frontend CI
on:
  push:
    paths: ["frontend/**"]
  pull_request:
    paths: ["frontend/**"]

jobs:
  build:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npm run build
```

- [ ] **Step 3: Commit**

```bash
git add contentflow/.github/
git commit -m "ci: add backend test and frontend build workflows"
```

---

## Task 14: End-to-End Verification

- [ ] **Step 1: Start backend**

```bash
cd contentflow/backend
cp .env.example .env  # Then edit .env to fill in your real API keys
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 2: Start frontend**

```bash
cd contentflow/frontend
npm run dev
```

- [ ] **Step 3: Verify full user flow**

1. Open `http://localhost:3000` → Landing page renders
2. Click "免费注册" → Register page, enter email + password → Redirect to /generate
3. Enter material text, select tone, click "生成小红书内容" → AI generates content, displays card
4. Navigate to "历史记录" → Shows generated content
5. Check sidebar → Shows "本月用量 1 / 10"
6. Generate 10 times → 11th attempt shows quota exceeded error

- [ ] **Step 4: Run all backend tests**

```bash
cd contentflow/backend && uv run pytest -v
```
Expected: All tests PASS

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: ContentFlow Phase 1 complete - MVP with XHS content generation"
```
