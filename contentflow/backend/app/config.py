from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/contentflow"
    test_database_url: str = "sqlite+aiosqlite:///./test.db"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 120
    jwt_refresh_expire_days: int = 7

    ominilink_api_key: str = ""
    dashscope_api_key: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    frontend_url: str = ""
    free_monthly_quota: int = 10

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
