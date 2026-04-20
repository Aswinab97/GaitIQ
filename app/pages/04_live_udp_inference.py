import streamlit as st
import pandas as pd
import numpy as np
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

st.set_page_config(page_title="GaitIQ - Live UDP Inference", layout="wide")
inject_global_styles()
render_sidebar()

st.title("Live UDP Inference")
st.caption("Receive IMU UDP stream and predict gait activity in real time")

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
    udp_port = st.number_input("UDP Port", min_value=1, max_value=65535, value=4210, step=1)
with c3:
    window_size = st.number_input("Feature window size", min_value=5, max_value=200, value=20, step=1)
with c4:
    refresh_ms = st.number_input("UI refresh (ms)", min_value=100, max_value=5000, value=500, step=100)

start_btn = st.button("Start Live Inference")
stop_btn = st.button("Stop")

if "running" not in st.session_state:
    st.session_state.running = False
if "rows" not in st.session_state:
    st.session_state.rows = deque(maxlen=3000)
if "pred_hist" not in st.session_state:
    st.session_state.pred_hist = deque(maxlen=200)

if start_btn:
    st.session_state.running = True
if stop_btn:
    st.session_state.running = False

def parse_udp_line(line: str):
    p = [x.strip() for x in line.split(",")]
    # accepted formats:
    # 3 cols: heading,roll,pitch
    # >=10 cols: time_ms,heading,roll,pitch,ax,ay,az,gx,gy,gz
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

    # raw latest values
    for c in base:
        feat[c] = float(df_tail[c].iloc[-1])

    # rolling mean/std (same logic as train script)
    for c in base:
        feat[f"{c}_mean"] = float(df_tail[c].mean())
        feat[f"{c}_std"] = float(df_tail[c].std(ddof=0) if len(df_tail) > 1 else 0.0)

    # Ensure exact feature order expected by model
    row = {c: feat.get(c, 0.0) for c in feature_cols}
    return pd.DataFrame([row], columns=feature_cols)

status_box = st.empty()
k1, k2, k3 = st.columns(3)
pred_box = k1.empty()
count_box = k2.empty()
rate_box = k3.empty()
chart_box = st.empty()
table_box = st.empty()

if st.session_state.running:
    status_box.success(f"Listening UDP on {udp_ip}:{udp_port}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((udp_ip, int(udp_port)))
    sock.settimeout(0.1)

    t0 = time.time()
    pkt_count = 0
    last_ui = 0.0

    try:
        while st.session_state.running:
            try:
                data, _ = sock.recvfrom(512)
                line = data.decode(errors="ignore").strip()
                row = parse_udp_line(line)
                if row is None:
                    continue

                row["pc_time"] = pd.Timestamp.now()
                st.session_state.rows.append(row)
                pkt_count += 1

                if len(st.session_state.rows) >= int(window_size):
                    df_live = pd.DataFrame(st.session_state.rows)
                    tail = df_live.tail(int(window_size)).copy()

                    x = build_feature_row(tail)
                    pred_id = model.predict(x.values)[0]
                    pred_label = label_encoder.inverse_transform([pred_id])[0]
                    st.session_state.pred_hist.append(
                        {"time": pd.Timestamp.now(), "predicted": pred_label}
                    )

                now = time.time()
                if (now - last_ui) * 1000 >= int(refresh_ms):
                    elapsed = max(now - t0, 1e-6)
                    hz = pkt_count / elapsed

                    latest_pred = st.session_state.pred_hist[-1]["predicted"] if st.session_state.pred_hist else "N/A"
                    pred_box.metric("Current Prediction", latest_pred)
                    count_box.metric("Packets Received", pkt_count)
                    rate_box.metric("Rate (Hz)", f"{hz:.1f}")

                    if st.session_state.pred_hist:
                        hist_df = pd.DataFrame(st.session_state.pred_hist)
                        dist = hist_df["predicted"].value_counts().rename_axis("class").reset_index(name="count")
                        chart = pd.DataFrame(dist)
                        chart_box.bar_chart(chart.set_index("class"))

                        table_box.dataframe(hist_df.tail(20), width="stretch")

                    last_ui = now

            except socket.timeout:
                pass

    except Exception as e:
        status_box.error(f"Runtime error: {e}")
    finally:
        sock.close()
        status_box.info("Stopped.")
else:
    status_box.info("Click 'Start Live Inference' to begin.")