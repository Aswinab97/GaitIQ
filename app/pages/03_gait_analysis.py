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
from app.components.layout import render_sidebar
from ml.features import extract_features, FEATURE_COLS as BASE_FEATURE_COLS

st.set_page_config(page_title="GaitIQ - Gait Analysis", layout="wide")
inject_global_styles()
render_sidebar()

st.title("Gait Analysis")
st.caption("Run terrain prediction on uploaded IMU session")

# -----------------------------
# Model paths
# -----------------------------
REAL_MODEL_PATH = ROOT / "ml" / "models" / "terrain_rf_real.joblib"
REAL_LABEL_PATH = ROOT / "ml" / "models" / "label_encoder_real.joblib"
REAL_FEATURES_PATH = ROOT / "ml" / "models" / "feature_cols_real.joblib"

OLD_MODEL_PATH = ROOT / "ml" / "models" / "terrain_rf.joblib"

# -----------------------------
# Load model (prefer real model)
# -----------------------------
model = None
label_encoder = None
model_name = None
model_feature_cols = None

if REAL_MODEL_PATH.exists() and REAL_LABEL_PATH.exists() and REAL_FEATURES_PATH.exists():
    model = joblib.load(REAL_MODEL_PATH)
    label_encoder = joblib.load(REAL_LABEL_PATH)
    model_feature_cols = joblib.load(REAL_FEATURES_PATH)
    model_name = "Real Model (terrain_rf_real.joblib)"
elif OLD_MODEL_PATH.exists():
    model = joblib.load(OLD_MODEL_PATH)
    label_encoder = None
    model_feature_cols = BASE_FEATURE_COLS
    model_name = "Fallback Synthetic Model (terrain_rf.joblib)"
else:
    st.error(
        f"No model found.\n\n"
        f"Expected one of:\n"
        f"- {REAL_MODEL_PATH}\n"
        f"- {OLD_MODEL_PATH}\n\n"
        f"Train first: python ml/train_real_classifier.py"
    )
    st.stop()

st.caption(f"Model in use: **{model_name}**")

# -----------------------------
# File input
# -----------------------------
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

# -----------------------------
# Feature extraction
# -----------------------------
try:
    feat_df = extract_features(df).copy()
except Exception as e:
    st.error(f"Feature extraction failed: {e}")
    st.stop()

# Ensure model-required features exist
for c in model_feature_cols:
    if c not in feat_df.columns:
        feat_df[c] = 0.0

X = feat_df[model_feature_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).values

# -----------------------------
# Predict
# -----------------------------
pred = model.predict(X)

if label_encoder is not None:
    # real model predicts encoded integers
    feat_df["predicted_terrain"] = label_encoder.inverse_transform(pred)
else:
    # fallback model likely predicts labels directly
    feat_df["predicted_terrain"] = pred

# -----------------------------
# Accuracy (if GT exists)
# -----------------------------
acc_val = None

# Choose a ground-truth column if present
gt_col = None
for c in ["terrain_label", "activity", "label"]:
    if c in feat_df.columns:
        gt_col = c
        break

if gt_col is not None:
    feat_df["correct"] = feat_df["predicted_terrain"].astype(str) == feat_df[gt_col].astype(str)
    acc_val = feat_df["correct"].mean() * 100

# -----------------------------
# KPIs
# -----------------------------
k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(
        f'<div class="kpi"><h4>Windows</h4><h2>{len(feat_df)}</h2><p>Total analyzed segments</p></div>',
        unsafe_allow_html=True
    )
with k2:
    classes = feat_df["predicted_terrain"].nunique()
    st.markdown(
        f'<div class="kpi"><h4>Predicted Classes</h4><h2>{classes}</h2><p>Unique terrains detected</p></div>',
        unsafe_allow_html=True
    )
with k3:
    if acc_val is not None:
        st.markdown(
            f'<div class="kpi"><h4>Window Accuracy</h4><h2>{acc_val:.1f}%</h2><p>Against available labels ({gt_col})</p></div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="kpi"><h4>Window Accuracy</h4><h2>N/A</h2><p>No ground-truth labels</p></div>',
            unsafe_allow_html=True
        )

# -----------------------------
# Distribution chart
# -----------------------------
st.markdown("### Predicted Terrain Distribution")
dist = feat_df["predicted_terrain"].value_counts().rename_axis("terrain").reset_index(name="count")
bar = px.bar(dist, x="terrain", y="count", title="Predicted windows per terrain", color="terrain")
bar.update_layout(template="plotly_dark", transition={"duration": 500})

st.markdown('<div class="section">', unsafe_allow_html=True)
st.plotly_chart(bar, width='stretch')
st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# Timeline table
# -----------------------------
st.markdown("### Prediction Timeline")
timeline_candidates = ["t_start", "t_end", "timestamp", gt_col, "predicted_terrain"]
timeline_cols = [c for c in timeline_candidates if c is not None and c in feat_df.columns]

st.markdown('<div class="section">', unsafe_allow_html=True)
if timeline_cols:
    st.dataframe(feat_df[timeline_cols], width='stretch')
else:
    st.dataframe(feat_df[["predicted_terrain"]], width='stretch')
st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# Feature preview
# -----------------------------
st.markdown("### Feature Preview")
st.markdown('<div class="section">', unsafe_allow_html=True)
st.dataframe(feat_df.head(20), width='stretch')
st.markdown('</div>', unsafe_allow_html=True)