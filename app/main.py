import streamlit as st
from pathlib import Path
import sys

# Ensure project root import works
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.components.theme import inject_global_styles
from app.components.layout import render_sidebar

st.set_page_config(
    page_title="GaitIQ",
    page_icon="🦿",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_styles()
render_sidebar()

# HERO
st.markdown(
    """
    <div class="hero">
      <div class="badge-live">● LIVE PROTOTYPE</div>
      <h1 style="margin-top:10px; margin-bottom:6px;">GaitIQ</h1>
      <p style="font-size:1.2rem; margin-top:0;">
        Smart prosthetic gait intelligence & fall-risk analytics platform
      </p>
      <p style="opacity:.85; margin-bottom:0;">
        Real-time sensor visualization • Feature extraction • Terrain classification
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# KPI ROW
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown('<div class="kpi"><h4>Pipeline</h4><h2>Active</h2><p>Data → Features → Model</p></div>', unsafe_allow_html=True)
with k2:
    st.markdown('<div class="kpi"><h4>Model</h4><h2>Ready</h2><p>RandomForest baseline</p></div>', unsafe_allow_html=True)
with k3:
    st.markdown('<div class="kpi"><h4>Sampling</h4><h2>100 Hz</h2><p>Window: 1s, 50% overlap</p></div>', unsafe_allow_html=True)
with k4:
    st.markdown('<div class="kpi"><h4>Deployment</h4><h2>Azure-ready</h2><p>Play Store path enabled</p></div>', unsafe_allow_html=True)

# SECTIONS
left, right = st.columns([1.25, 1])

with left:
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("Platform Overview")
    st.write(
        """
GaitIQ is an intelligent prosthetic analytics platform that transforms IMU time-series
into clinically meaningful insights. The system supports:
- **Signal ingestion** from synthetic/live sessions
- **Automated feature extraction** (cadence, variability, motion stats)
- **Terrain prediction** using a trained baseline classifier
- **Dashboard-driven interpretation** for faster engineering and clinical iteration
"""
    )
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("Quick Navigation")
    st.markdown(
        """
- **Live Dashboard** → Upload and inspect raw signals  
- **Gait Analysis** → Run ML predictions per window  
- **Main Page** → Product summary + readiness status
"""
    )
    st.info("Tip: Open the sidebar to switch between pages.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("### Development Roadmap")
r1, r2, r3 = st.columns(3)
with r1:
    st.markdown('<div class="section"><b>Phase 1</b><br/>Data + UI foundation ✅</div>', unsafe_allow_html=True)
with r2:
    st.markdown('<div class="section"><b>Phase 2</b><br/>Live serial ingestion + risk scoring 🚧</div>', unsafe_allow_html=True)
with r3:
    st.markdown('<div class="section"><b>Phase 3</b><br/>Cloud deployment + mobile wrapper 📦</div>', unsafe_allow_html=True)

st.caption("GaitIQ • Engineering Prototype v0.2")