import streamlit as st

st.set_page_config(page_title="GaitIQ", page_icon="🦿", layout="wide")

st.title("GaitIQ")
st.subheader("Smart prosthetic gait & fall-risk analyzer")
st.caption("Engineering prototype · v0.1.0-alpha")

st.markdown("---")

col1, col2, col3 = st.columns(3)
col1.metric("Pipeline Status", "Initialized")
col2.metric("Data Source", "No file uploaded")
col3.metric("Model Status", "Not trained")

st.markdown("### Next Steps")
st.markdown(
    """
1. Add synthetic data generator (`data/synthetic/generate_synthetic.py`)
2. Add CSV upload + plotting page
3. Add feature extraction + baseline classifier
4. Integrate hardware stream when components arrive
"""
)

st.info("Project is set up correctly. You are ready to build Phase 1.")