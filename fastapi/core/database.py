from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from core.config import settings

engine = create_engine(
    settings.sqlalchemy_url(),
    connect_args={"check_same_thread": False} if settings.sqlalchemy_url().startswith("sqlite") else {},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    import models  # noqa: F401 确保模型注册

    Base.metadata.create_all(bind=engine)
