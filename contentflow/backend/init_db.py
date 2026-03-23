"""本地开发用：创建 SQLite 数据库表"""
import asyncio
from app.database import engine, Base
from app.models import *  # noqa

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("数据库表创建完成")

asyncio.run(main())
