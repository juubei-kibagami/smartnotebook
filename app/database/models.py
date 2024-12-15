from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

import os
from dotenv import load_dotenv

load_dotenv()
engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')  # подключение и создание бд

async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger)


class Note(Base):
    __tablename__ = 'notes'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger)
    note: Mapped[str] = mapped_column(String(200))


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # создание всех таблиц
