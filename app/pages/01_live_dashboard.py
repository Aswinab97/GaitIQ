import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="GaitIQ - Live Dashboard", layout="wide")
st.title("Live Dashboard")
st.caption("Upload IMU CSV and inspect gait signals")

required_cols = [
    "timestamp","ax","ay","az","gx","gy","gz","roll","pitch","yaw","terrain_label"
]

uploaded = st.file_uploader("Upload session CSV", type=["csv"])

df = None
if uploaded is not None:
    df = pd.read_csv(uploaded)
    st.success("CSV uploaded successfully.")
else:
    # fallback to synthetic example if available
    try:
        df = pd.read_csv("data/synthetic/session_synthetic_v1.csv")
        st.info("Using local synthetic file: data/synthetic/session_synthetic_v1.csv")
    except Exception:
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
c1.metric("Samples", f"{samples}")
c2.metric("Duration (s)", f"{duration_sec:.1f}")
c3.metric("Terrain classes", f"{terrains}")

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
    title=f"{signal_group} vs Time"
)
st.plotly_chart(fig, width="stretch")

st.markdown("### Terrain Label Distribution")
dist = df["terrain_label"].value_counts().reset_index()
dist.columns = ["terrain_label", "count"]
bar = px.bar(dist, x="terrain_label", y="count", title="Samples per Terrain")
st.plotly_chart(bar, width="stretch")

st.markdown("### Preview")
st.dataframe(df.head(20), width="stretch")