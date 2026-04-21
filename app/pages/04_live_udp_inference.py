import streamlit as st
import pandas as pd
import socket
import time
import joblib
from pathlib import Path
import sys
from collections import deque

# Ensure project root imports work
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.components.theme import inject_global_styles
from app.components.layout import render_sidebar
from core.session.repository import (
    init_db,
    create_live_session,
    end_live_session,
    add_prediction,
    add_event,
)

st.set_page_config(page_title="GaitIQ - Live UDP Inference", layout="wide")
inject_global_styles()
render_sidebar()

st.title("Live UDP Inference")
st.caption("Receive IMU UDP stream and predict gait activity in real time")

init_db()

REAL_MODEL_PATH = ROOT / "ml" / "models" / "terrain_rf_real.joblib"
REAL_LABEL_PATH = ROOT / "ml" / "models" / "label_encoder_real.joblib"
REAL_FEATURES_PATH = ROOT / "ml" / "models" / "feature_cols_real.joblib"

if not (REAL_MODEL_PATH.exists() and REAL_LABEL_PATH.exists() and REAL_FEATURES_PATH.exists()):
    st.error("Real model files not found. Train first: python ml/train_real_classifier.py")
    st.stop()

model = joblib.load(REAL_MODEL_PATH)
label_encoder = joblib.load(REAL_LABEL_PATH)
feature_cols = joblib.load(REAL_FEATURES_PATH)

# ---- Controls ----
c1, c2, c3, c4 = st.columns(4)
with c1:
    udp_ip = st.text_input("UDP bind IP", "0.0.0.0")
with c2:
    udp_port = st.number_input("UDP Port", min_value=1, max_value=65535, value=5005, step=1)
with c3:
    window_size = st.number_input("Feature window size", min_value=5, max_value=200, value=20, step=1)
with c4:
    refresh_ms = st.number_input("UI refresh (ms)", min_value=100, max_value=5000, value=500, step=100)

start_btn = st.button("Start Live Inference")
stop_btn = st.button("Stop")

# ---- Session state ----
if "running" not in st.session_state:
    st.session_state.running = False
if "rows" not in st.session_state:
    st.session_state.rows = deque(maxlen=3000)
if "pred_hist" not in st.session_state:
    st.session_state.pred_hist = deque(maxlen=200)
if "udp_sock" not in st.session_state:
    st.session_state.udp_sock = None
if "udp_target" not in st.session_state:
    st.session_state.udp_target = None
if "pkt_count" not in st.session_state:
    st.session_state.pkt_count = 0
if "t0" not in st.session_state:
    st.session_state.t0 = None
if "live_session_id" not in st.session_state:
    st.session_state.live_session_id = None
if "last_pred_label" not in st.session_state:
    st.session_state.last_pred_label = None

def close_udp_socket():
    if st.session_state.udp_sock is not None:
        try:
            st.session_state.udp_sock.close()
        except Exception:
            pass
    st.session_state.udp_sock = None
    st.session_state.udp_target = None

def open_udp_socket(ip: str, port: int):
    close_udp_socket()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((ip, int(port)))
    sock.settimeout(0.05)
    st.session_state.udp_sock = sock
    st.session_state.udp_target = (ip, int(port))

def parse_udp_line(line: str):
    p = [x.strip() for x in line.split(",")]
    if len(p) == 3:
        return {
            "heading": float(p[0]), "roll": float(p[1]), "pitch": float(p[2]),
            "ax": 0.0, "ay": 0.0, "az": 0.0, "gx": 0.0, "gy": 0.0, "gz": 0.0
        }
    if len(p) >= 10:
        return {
            "heading": float(p[1]), "roll": float(p[2]), "pitch": float(p[3]),
            "ax": float(p[4]), "ay": float(p[5]), "az": float(p[6]),
            "gx": float(p[7]), "gy": float(p[8]), "gz": float(p[9]),
        }
    return None

def build_feature_row(df_tail: pd.DataFrame):
    base = ["heading","roll","pitch","ax","ay","az","gx","gy","gz"]
    feat = {}

    for c in base:
        feat[c] = float(df_tail[c].iloc[-1])

    for c in base:
        feat[f"{c}_mean"] = float(df_tail[c].mean())
        feat[f"{c}_std"] = float(df_tail[c].std(ddof=0) if len(df_tail) > 1 else 0.0)

    row = {c: feat.get(c, 0.0) for c in feature_cols}
    return pd.DataFrame([row], columns=feature_cols)

# ---- Start/Stop actions ----
if start_btn:
    target = (udp_ip, int(udp_port))
    need_rebind = (
        (not st.session_state.running)
        or (st.session_state.udp_target != target)
        or (st.session_state.udp_sock is None)
    )
    if need_rebind:
        try:
            open_udp_socket(udp_ip, int(udp_port))
            st.session_state.pkt_count = 0
            st.session_state.t0 = time.time()
            st.session_state.last_pred_label = None

            st.session_state.live_session_id = create_live_session(
                device_id=f"{udp_ip}:{udp_port}",
                sample_rate_hz=None,
                model_version="terrain_rf_real.joblib",
                notes="Live UDP inference session"
            )
            add_event(
                session_id=st.session_state.live_session_id,
                event_type="session_started",
                payload_json={"udp_ip": udp_ip, "udp_port": int(udp_port)}
            )
        except OSError as e:
            st.error(f"Could not bind UDP socket on {udp_ip}:{udp_port} -> {e}")
            st.session_state.running = False

    st.session_state.running = st.session_state.udp_sock is not None

if stop_btn:
    st.session_state.running = False
    close_udp_socket()
    if st.session_state.live_session_id is not None:
        add_event(st.session_state.live_session_id, "session_stopped", {})
        end_live_session(st.session_state.live_session_id)
        st.session_state.live_session_id = None

# ---- UI placeholders ----
status_box = st.empty()
k1, k2, k3 = st.columns(3)
pred_box = k1.empty()
count_box = k2.empty()
rate_box = k3.empty()
chart_box = st.empty()
table_box = st.empty()

if st.session_state.running and st.session_state.udp_sock is not None:
    ip, port = st.session_state.udp_target
    status_box.success(f"Listening UDP on {ip}:{port}")

    for _ in range(300):
        try:
            data, _ = st.session_state.udp_sock.recvfrom(512)
            line = data.decode(errors="ignore").strip()
            row = parse_udp_line(line)
            if row is None:
                continue

            row["pc_time"] = pd.Timestamp.now()
            st.session_state.rows.append(row)
            st.session_state.pkt_count += 1

            if len(st.session_state.rows) >= int(window_size):
                df_live = pd.DataFrame(st.session_state.rows)
                tail = df_live.tail(int(window_size)).copy()
                x = build_feature_row(tail)

                pred_id = model.predict(x.values)[0]
                pred_label = label_encoder.inverse_transform([pred_id])[0]
                pred_time = pd.Timestamp.now()

                st.session_state.pred_hist.append({"time": pred_time, "predicted": pred_label})

                if st.session_state.live_session_id is not None:
                    add_prediction(
                        session_id=st.session_state.live_session_id,
                        predicted_terrain=str(pred_label),
                        confidence=None,
                        fall_risk_score=None,
                        meta={"window_size": int(window_size)}
                    )

                    if st.session_state.last_pred_label is not None and st.session_state.last_pred_label != pred_label:
                        add_event(
                            session_id=st.session_state.live_session_id,
                            event_type="terrain_transition",
                            payload_json={
                                "from": str(st.session_state.last_pred_label),
                                "to": str(pred_label),
                                "at": str(pred_time),
                            },
                        )

                st.session_state.last_pred_label = pred_label

        except socket.timeout:
            break
        except Exception as e:
            status_box.error(f"Runtime error: {e}")
            st.session_state.running = False
            close_udp_socket()
            if st.session_state.live_session_id is not None:
                add_event(st.session_state.live_session_id, "runtime_error", {"error": str(e)})
                end_live_session(st.session_state.live_session_id)
                st.session_state.live_session_id = None
            break

    elapsed = max(time.time() - (st.session_state.t0 or time.time()), 1e-6)
    hz = st.session_state.pkt_count / elapsed
    latest_pred = st.session_state.pred_hist[-1]["predicted"] if st.session_state.pred_hist else "N/A"

    pred_box.metric("Current Prediction", latest_pred)
    count_box.metric("Packets Received", st.session_state.pkt_count)
    rate_box.metric("Rate (Hz)", f"{hz:.1f}")

    if st.session_state.pred_hist:
        hist_df = pd.DataFrame(st.session_state.pred_hist)
        dist = hist_df["predicted"].value_counts().rename_axis("class").reset_index(name="count")
        chart_box.bar_chart(dist.set_index("class"))
        table_box.dataframe(hist_df.tail(20), width="stretch")

    time.sleep(max(int(refresh_ms), 100) / 1000.0)
    st.rerun()
else:
    status_box.info("Click 'Start Live Inference' to begin.")