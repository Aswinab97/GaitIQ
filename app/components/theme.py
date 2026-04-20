import streamlit as st

def inject_global_styles():
    st.markdown("""
    <style>
    /* Page canvas */
    .main {
      background: linear-gradient(180deg, #0B1020 0%, #0F172A 100%);
    }

    /* App width + spacing */
    .block-container {
      max-width: 1200px;
      padding-top: 1.2rem;
      padding-bottom: 2rem;
    }

    /* Hero banner */
    .hero {
      padding: 28px;
      border-radius: 20px;
      background: linear-gradient(135deg, rgba(0,229,168,0.18), rgba(76,110,245,0.18));
      border: 1px solid rgba(255,255,255,0.12);
      box-shadow: 0 10px 30px rgba(0,0,0,0.25);
      margin-bottom: 14px;
    }

    /* Glass section card */
    .section {
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.10);
      border-radius: 16px;
      padding: 14px;
      margin-top: 10px;
    }

    /* KPI cards */
    .kpi {
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 16px;
      padding: 14px 16px;
      transition: transform .2s ease, box-shadow .2s ease;
    }
    .kpi:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(0,0,0,.25);
    }

    /* Live badge */
    .badge-live {
      display: inline-block;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(0,229,168,.18);
      color: #7CFFD6;
      border: 1px solid rgba(0,229,168,.45);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: .2px;
    }
    </style>
    """, unsafe_allow_html=True)
