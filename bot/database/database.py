import os

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot.database.models import Base

# Берем URL из .env, если его нет — используем дефолтный
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///cv_bot.db")

# Создаем асинхронный движок
engine = create_async_engine(DATABASE_URL, echo=False)

# Фабрика сессий для работы с БД в хэндлерах
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def init_db():
    """Создает таблицы в базе данных при запуске бота"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)