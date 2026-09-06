"""Schéma persistant des stations et hauteurs de neige quotidiennes."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from snow_layers.database import Base


class Station(Base):
    __tablename__ = "stations"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    elevation_m: Mapped[float] = mapped_column(Float)
    observations: Mapped[list["SnowObservation"]] = relationship(back_populates="station")


class SnowObservation(Base):
    __tablename__ = "snow_observations"
    __table_args__ = (UniqueConstraint("station_id", "observed_on", "source", name="uq_snow_observation"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), index=True)
    observed_on: Mapped[date] = mapped_column(Date, index=True)
    snow_depth_cm: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(80))
    source_url: Mapped[str] = mapped_column(String(500))
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    station: Mapped[Station] = relationship(back_populates="observations")
