import sqlite3
import pandas as pd
import streamlit as st
from pathlib import Path

DB_PATH = Path("gaitiq.db")


def load_sessions_df() -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT
            s.id,
            s.device_id,
            s.user_id,
            s.started_at,
            s.ended_at,
            s.sample_rate_hz,
            s.model_version,
            s.notes,
            COUNT(DISTINCT p.id) AS prediction_count,
            COUNT(DISTINCT e.id) AS event_count
        FROM sessions s
        LEFT JOIN predictions p ON p.session_id = s.id
        LEFT JOIN events e ON e.session_id = s.id
        GROUP BY s.id
        ORDER BY s.started_at DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def load_predictions_df(session_id: int) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT id, session_id, t, predicted_activity, predicted_terrain, confidence, fall_risk_score, meta
        FROM predictions
        WHERE session_id = ?
        ORDER BY t ASC
    """
    df = pd.read_sql_query(query, conn, params=(session_id,))
    conn.close()
    return df


def load_events_df(session_id: int) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT id, session_id, t, event_type, payload_json
        FROM events
        WHERE session_id = ?
        ORDER BY t ASC
    """
    df = pd.read_sql_query(query, conn, params=(session_id,))
    conn.close()
    return df


def app():
    st.title("📊 Session History (Database)")

    if not DB_PATH.exists():
        st.warning("Database not found yet: gaitiq.db")
        st.info("Run a live session first from '04_live_udp_inference.py'.")
        return

    sessions_df = load_sessions_df()

    if sessions_df.empty:
        st.info("No sessions found in database.")
        return

    st.subheader("All Sessions")
    st.dataframe(sessions_df, width="stretch")

    session_ids = sessions_df["id"].tolist()
    selected_id = st.selectbox("Select Session ID", session_ids)

    selected_row = sessions_df[sessions_df["id"] == selected_id].iloc[0]

    st.subheader("📌 Session Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Session ID", int(selected_row["id"]))
    c2.metric("Predictions", int(selected_row["prediction_count"]))
    c3.metric("Events", int(selected_row["event_count"]))
    c4.metric("Model", str(selected_row["model_version"]) if pd.notna(selected_row["model_version"]) else "N/A")

    st.write("**Started at:**", selected_row["started_at"])
    st.write("**Ended at:**", selected_row["ended_at"] if pd.notna(selected_row["ended_at"]) else "Running / not closed")
    st.write("**Device:**", selected_row["device_id"] if pd.notna(selected_row["device_id"]) else "N/A")
    st.write("**User:**", selected_row["user_id"] if pd.notna(selected_row["user_id"]) else "N/A")
    st.write("**Notes:**", selected_row["notes"] if pd.notna(selected_row["notes"]) else "")

    pred_df = load_predictions_df(int(selected_id))
    evt_df = load_events_df(int(selected_id))

    st.subheader("🧠 Predictions")
    if pred_df.empty:
        st.info("No predictions recorded for this session.")
    else:
        st.dataframe(pred_df.tail(200), width="stretch")

        if "predicted_terrain" in pred_df.columns and pred_df["predicted_terrain"].notna().any():
            dist = (
                pred_df["predicted_terrain"]
                .value_counts()
                .rename_axis("terrain")
                .reset_index(name="count")
            )
            st.bar_chart(dist.set_index("terrain"))

        if "fall_risk_score" in pred_df.columns and pred_df["fall_risk_score"].notna().any():
            risk_plot = pred_df.copy()
            risk_plot["t"] = pd.to_datetime(risk_plot["t"], errors="coerce")
            risk_plot = risk_plot.dropna(subset=["t"])
            st.line_chart(risk_plot.set_index("t")["fall_risk_score"])

    st.subheader("⚠️ Events")
    if evt_df.empty:
        st.info("No events recorded for this session.")
    else:
        st.dataframe(evt_df.tail(200), width="stretch")


if __name__ == "__main__":
    app()