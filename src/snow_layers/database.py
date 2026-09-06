"""Configuration SQLite et cycle de vie des sessions SQLAlchemy."""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = f"sqlite:///{PROJECT_ROOT / 'data' / 'snow_layers.sqlite'}"


class Base(DeclarativeBase):
    """Base déclarative commune aux modèles persistés."""


def database_url() -> str:
    return os.environ.get("SNOW_LAYERS_DATABASE_URL", DEFAULT_DATABASE_URL)


def create_session_factory(url: str | None = None):
    engine = create_engine(url or database_url())
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)
