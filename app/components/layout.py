import streamlit as st

def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div style="
                padding:14px 12px;
                border-radius:14px;
                background: linear-gradient(135deg, rgba(0,229,168,0.18), rgba(76,110,245,0.18));
                border:1px solid rgba(255,255,255,0.12);
                margin-bottom:12px;">
              <div style="font-size:0.8rem; opacity:.9;">Gait Intelligence Platform</div>
              <div style="font-size:1.35rem; font-weight:800; margin-top:2px;">🦿 GaitIQ</div>
              <div style="font-size:0.78rem; opacity:.8; margin-top:6px;">Real-time prosthetic analytics</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### System Status")
        st.markdown("- 🟢 Data Pipeline: **Online**")
        st.markdown("- 🟢 Feature Engine: **Ready**")
        st.markdown("- 🟢 Classifier: **Loaded**")
        st.markdown("- 🟡 Live Device: **Simulated**")

        st.markdown("---")
        st.markdown("### Quick Links")
        st.markdown("- Home")
        st.markdown("- Live Dashboard")
        st.markdown("- Gait Analysis")

        st.markdown("---")
        st.caption("GaitIQ v0.2 • Built by Aswin")
