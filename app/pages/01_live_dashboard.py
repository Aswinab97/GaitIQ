import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys

# Ensure project root imports work
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.components.theme import inject_global_styles
from app.components.layout import render_sidebar

st.set_page_config(page_title="GaitIQ - Live Dashboard", layout="wide")
inject_global_styles()
render_sidebar()

st.title("Live Dashboard")
st.caption("Upload IMU CSV and inspect gait signals")

required_cols = [
    "timestamp", "ax", "ay", "az",
    "gx", "gy", "gz",
    "roll", "pitch", "yaw",
    "terrain_label"
]

uploaded = st.file_uploader("Upload session CSV", type=["csv"])

if uploaded is not None:
    df = pd.read_csv(uploaded)
    st.success("CSV uploaded successfully.")
else:
    sample_path = ROOT / "data" / "synthetic" / "session_synthetic_v1.csv"
    if sample_path.exists():
        df = pd.read_csv(sample_path)
        st.info(f"Using local synthetic file: {sample_path}")
    else:
        st.warning("Upload a CSV to continue.")
        st.stop()

missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"Missing required columns: {missing}")
    st.stop()

# basic stats
duration_sec = (df["timestamp"].iloc[-1] - df["timestamp"].iloc[0]) / 1000.0
samples = len(df)
terrains = df["terrain_label"].nunique()

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f'<div class="kpi"><h4>Samples</h4><h2>{samples}</h2><p>Total rows ingested</p></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="kpi"><h4>Duration</h4><h2>{duration_sec:.1f}s</h2><p>Session length</p></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="kpi"><h4>Terrain Classes</h4><h2>{terrains}</h2><p>Unique labels</p></div>', unsafe_allow_html=True)

st.markdown("### Signal Viewer")
signal_group = st.radio("Choose signal group", ["Acceleration", "Gyroscope", "Orientation"], horizontal=True)

plot_df = df.copy()
plot_df["time_s"] = (plot_df["timestamp"] - plot_df["timestamp"].iloc[0]) / 1000.0

if signal_group == "Acceleration":
    y_cols = ["ax", "ay", "az"]
elif signal_group == "Gyroscope":
    y_cols = ["gx", "gy", "gz"]
else:
    y_cols = ["roll", "pitch", "yaw"]

long_df = plot_df.melt(
    id_vars=["time_s", "terrain_label"],
    value_vars=y_cols,
    var_name="signal",
    value_name="value"
)

fig = px.line(
    long_df,
    x="time_s",
    y="value",
    color="signal",
    title=f"{signal_group} vs Time",
)
fig.update_layout(
    template="plotly_dark",
    transition={"duration": 500},
    hovermode="x unified",
    legend_title_text="Signal",
)

st.markdown('<div class="section">', unsafe_allow_html=True)
st.plotly_chart(fig, width='stretch')
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("### Terrain Label Distribution")
dist = df["terrain_label"].value_counts().reset_index()
dist.columns = ["terrain_label", "count"]
bar = px.bar(dist, x="terrain_label", y="count", title="Samples per Terrain")
bar.update_layout(
    template="plotly_dark",
    transition={"duration": 500},
    xaxis_title="Terrain",
    yaxis_title="Count",
)

st.markdown('<div class="section">', unsafe_allow_html=True)
st.plotly_chart(bar, width='stretch')
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("### Preview")
st.markdown('<div class="section">', unsafe_allow_html=True)
st.dataframe(df.head(20), width='stretch')
st.markdown('</div>', unsafe_allow_html=True)