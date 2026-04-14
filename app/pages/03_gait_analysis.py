import streamlit as st
import pandas as pd
import joblib
from pathlib import Path
import sys

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Local import after path fix
from ml.features import extract_features, FEATURE_COLS

st.set_page_config(page_title="GaitIQ - Gait Analysis", layout="wide")
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

if "terrain_label" in feat_df.columns:
    feat_df["correct"] = feat_df["predicted_terrain"] == feat_df["terrain_label"]
    st.metric("Window-level Accuracy", f"{feat_df['correct'].mean() * 100:.1f}%")

st.markdown("### Predicted Terrain Distribution")
dist = feat_df["predicted_terrain"].value_counts().rename_axis("terrain").reset_index(name="count")
st.bar_chart(dist.set_index("terrain"))

st.markdown("### Prediction Timeline")
cols = [c for c in ["t_start", "t_end", "terrain_label", "predicted_terrain"] if c in feat_df.columns]
st.dataframe(feat_df[cols], width="stretch")

st.markdown("### Feature Preview")
st.dataframe(feat_df.head(20), width="stretch")