from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.session.models import Base, Session, Prediction, Event


DB_PATH = Path("gaitiq.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def create_live_session(
    device_id: Optional[str] = None,
    user_id: Optional[str] = None,
    sample_rate_hz: Optional[float] = None,
    model_version: Optional[str] = None,
    notes: Optional[str] = None,
) -> int:
    with SessionLocal() as db:
        s = Session(
            device_id=device_id,
            user_id=user_id,
            started_at=datetime.now(timezone.utc),
            sample_rate_hz=sample_rate_hz,
            model_version=model_version,
            notes=notes,
        )
        db.add(s)
        db.commit()
        db.refresh(s)
        return s.id


def end_live_session(session_id: int) -> None:
    with SessionLocal() as db:
        s = db.get(Session, session_id)
        if s is None:
            return
        s.ended_at = datetime.now(timezone.utc)
        db.commit()


def add_prediction(
    session_id: int,
    predicted_terrain: Optional[str],
    confidence: Optional[float] = None,
    fall_risk_score: Optional[float] = None,
    meta: Optional[dict] = None,
) -> None:
    with SessionLocal() as db:
        p = Prediction(
            session_id=session_id,
            t=datetime.now(timezone.utc),
            predicted_terrain=predicted_terrain,
            confidence=confidence,
            fall_risk_score=fall_risk_score,
            meta=meta or {},
        )
        db.add(p)
        db.commit()


def add_event(
    session_id: int,
    event_type: str,
    payload_json: Optional[dict] = None,
) -> None:
    with SessionLocal() as db:
        e = Event(
            session_id=session_id,
            t=datetime.now(timezone.utc),
            event_type=event_type,
            payload_json=payload_json or {},
        )
        db.add(e)
        db.commit()