import streamlit as st
import pandas as pd
import joblib
import plotly.express as px
from pathlib import Path
import sys

# Ensure project root imports work
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.components.theme import inject_global_styles
from ml.features import extract_features, FEATURE_COLS

st.set_page_config(page_title="GaitIQ - Gait Analysis", layout="wide")
inject_global_styles()

st.title("Gait Analysis")
st.caption("Run terrain prediction on uploaded IMU session")

MODEL_PATH = ROOT / "ml" / "models" / "terrain_rf.joblib"

required_cols = [
    "timestamp", "ax", "ay", "az",
    "gx", "gy", "gz",
    "roll", "pitch", "yaw",
    "terrain_label"
]

uploaded = st.file_uploader("Upload session CSV", type=["csv"])

if uploaded is not None:
    df = pd.read_csv(uploaded)
    st.success("CSV uploaded.")
else:
    sample_path = ROOT / "data" / "synthetic" / "session_synthetic_v1.csv"
    if sample_path.exists():
        df = pd.read_csv(sample_path)
        st.info(f"Using synthetic sample: {sample_path}")
    else:
        st.warning("Upload a CSV to continue.")
        st.stop()

missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"Missing required columns: {missing}")
    st.stop()

if not MODEL_PATH.exists():
    st.error(f"Model not found at {MODEL_PATH}. Run: python ml/terrain_classifier.py")
    st.stop()

model = joblib.load(MODEL_PATH)

feat_df = extract_features(df)
X = feat_df[FEATURE_COLS]
feat_df["predicted_terrain"] = model.predict(X)

# KPI row
acc_val = None
if "terrain_label" in feat_df.columns:
    feat_df["correct"] = feat_df["predicted_terrain"] == feat_df["terrain_label"]
    acc_val = feat_df["correct"].mean() * 100

k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(f'<div class="kpi"><h4>Windows</h4><h2>{len(feat_df)}</h2><p>Total analyzed segments</p></div>', unsafe_allow_html=True)
with k2:
    classes = feat_df["predicted_terrain"].nunique()
    st.markdown(f'<div class="kpi"><h4>Predicted Classes</h4><h2>{classes}</h2><p>Unique terrains detected</p></div>', unsafe_allow_html=True)
with k3:
    if acc_val is not None:
        st.markdown(f'<div class="kpi"><h4>Window Accuracy</h4><h2>{acc_val:.1f}%</h2><p>Against available labels</p></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="kpi"><h4>Window Accuracy</h4><h2>N/A</h2><p>No ground-truth labels</p></div>', unsafe_allow_html=True)

st.markdown("### Predicted Terrain Distribution")
dist = feat_df["predicted_terrain"].value_counts().rename_axis("terrain").reset_index(name="count")
bar = px.bar(dist, x="terrain", y="count", title="Predicted windows per terrain", color="terrain")
bar.update_layout(template="plotly_dark", transition={"duration": 500})
st.markdown('<div class="section">', unsafe_allow_html=True)
st.plotly_chart(bar, width="stretch")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("### Prediction Timeline")
timeline_cols = [c for c in ["t_start", "t_end", "terrain_label", "predicted_terrain"] if c in feat_df.columns]
st.markdown('<div class="section">', unsafe_allow_html=True)
st.dataframe(feat_df[timeline_cols], width="stretch")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("### Feature Preview")
st.markdown('<div class="section">', unsafe_allow_html=True)
st.dataframe(feat_df.head(20), width="stretch")
st.markdown('</div>', unsafe_allow_html=True)