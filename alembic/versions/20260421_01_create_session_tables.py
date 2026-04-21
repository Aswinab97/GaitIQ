"""create session tracking tables

Revision ID: 20260421_01
Revises:
Create Date: 2026-04-21 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260421_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("device_id", sa.String(length=128), nullable=True),
        sa.Column("user_id", sa.String(length=128), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sample_rate_hz", sa.Float(), nullable=True),
        sa.Column("model_version", sa.String(length=128), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sessions_device_id", "sessions", ["device_id"], unique=False)
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"], unique=False)
    op.create_index("ix_sessions_started_at", "sessions", ["started_at"], unique=False)
    op.create_index("ix_sessions_ended_at", "sessions", ["ended_at"], unique=False)
    op.create_index("ix_sessions_model_version", "sessions", ["model_version"], unique=False)
    op.create_index("ix_sessions_started_ended", "sessions", ["started_at", "ended_at"], unique=False)

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("t", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("predicted_activity", sa.String(length=64), nullable=True),
        sa.Column("predicted_terrain", sa.String(length=64), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("fall_risk_score", sa.Float(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_predictions_session_id", "predictions", ["session_id"], unique=False)
    op.create_index("ix_predictions_t", "predictions", ["t"], unique=False)
    op.create_index("ix_predictions_predicted_activity", "predictions", ["predicted_activity"], unique=False)
    op.create_index("ix_predictions_predicted_terrain", "predictions", ["predicted_terrain"], unique=False)
    op.create_index("ix_predictions_fall_risk_score", "predictions", ["fall_risk_score"], unique=False)
    op.create_index("ix_predictions_session_t", "predictions", ["session_id", "t"], unique=False)

    op.create_table(
        "segments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("t_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("t_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("features_json", sa.JSON(), nullable=True),
        sa.Column("quality_flags", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_segments_session_id", "segments", ["session_id"], unique=False)
    op.create_index("ix_segments_t_start", "segments", ["t_start"], unique=False)
    op.create_index("ix_segments_t_end", "segments", ["t_end"], unique=False)
    op.create_index("ix_segments_session_tstart_tend", "segments", ["session_id", "t_start", "t_end"], unique=False)

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("t", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_events_session_id", "events", ["session_id"], unique=False)
    op.create_index("ix_events_t", "events", ["t"], unique=False)
    op.create_index("ix_events_event_type", "events", ["event_type"], unique=False)
    op.create_index("ix_events_session_t", "events", ["session_id", "t"], unique=False)
    op.create_index("ix_events_session_type_t", "events", ["session_id", "event_type", "t"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_events_session_type_t", table_name="events")
    op.drop_index("ix_events_session_t", table_name="events")
    op.drop_index("ix_events_event_type", table_name="events")
    op.drop_index("ix_events_t", table_name="events")
    op.drop_index("ix_events_session_id", table_name="events")
    op.drop_table("events")

    op.drop_index("ix_segments_session_tstart_tend", table_name="segments")
    op.drop_index("ix_segments_t_end", table_name="segments")
    op.drop_index("ix_segments_t_start", table_name="segments")
    op.drop_index("ix_segments_session_id", table_name="segments")
    op.drop_table("segments")

    op.drop_index("ix_predictions_session_t", table_name="predictions")
    op.drop_index("ix_predictions_fall_risk_score", table_name="predictions")
    op.drop_index("ix_predictions_predicted_terrain", table_name="predictions")
    op.drop_index("ix_predictions_predicted_activity", table_name="predictions")
    op.drop_index("ix_predictions_t", table_name="predictions")
    op.drop_index("ix_predictions_session_id", table_name="predictions")
    op.drop_table("predictions")

    op.drop_index("ix_sessions_started_ended", table_name="sessions")
    op.drop_index("ix_sessions_model_version", table_name="sessions")
    op.drop_index("ix_sessions_ended_at", table_name="sessions")
    op.drop_index("ix_sessions_started_at", table_name="sessions")
    op.drop_index("ix_sessions_user_id", table_name="sessions")
    op.drop_index("ix_sessions_device_id", table_name="sessions")
    op.drop_table("sessions")
