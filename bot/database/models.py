from sqlalchemy import BigInteger, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # Сюда мы будем сохранять Pydantic-схему CandidateProfile в виде JSON-строки
    profile_data: Mapped[str] = mapped_column(Text, nullable=True)