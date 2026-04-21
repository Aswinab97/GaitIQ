from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # device/user identity (keep nullable for prototype flexibility)
    device_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    sample_rate_hz: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    segments: Mapped[list["Segment"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    events: Mapped[list["Event"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_sessions_started_ended", "started_at", "ended_at"),
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # event timestamp (wall clock)
    t: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    predicted_activity: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    predicted_terrain: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    # confidence of primary prediction [0,1]
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # fall risk score [0,100]
    fall_risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)

    # optional richer payload for explainability/prototyping
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    session: Mapped["Session"] = relationship(back_populates="predictions")

    __table_args__ = (
        Index("ix_predictions_session_t", "session_id", "t"),
    )


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # segment bounds (sensor/window time or wall-clock if sensor time missing)
    t_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    t_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # serialized feature vector snapshot
    features_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # e.g. {"packet_loss":0.02, "missing_fields":["gx"]}
    quality_flags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    session: Mapped["Session"] = relationship(back_populates="segments")

    __table_args__ = (
        Index("ix_segments_session_tstart_tend", "session_id", "t_start", "t_end"),
    )


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    t: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    # terrain_transition, activity_transition, risk_alert, instability, etc.
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    payload_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    session: Mapped["Session"] = relationship(back_populates="events")

    __table_args__ = (
        Index("ix_events_session_t", "session_id", "t"),
        Index("ix_events_session_type_t", "session_id", "event_type", "t"),
    )