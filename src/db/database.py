from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from configs.config import config


engine = create_engine(config.db.url, echo=config.db.echo, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from src.db.models import (  # noqa: F401
        Project, RegressionCycle, BugReport,
        ClassificationAuditLog, ModelVersion, User,
    )
    Base.metadata.create_all(bind=engine)
