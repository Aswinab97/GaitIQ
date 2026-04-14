# GaitIQ
**Smart prosthetic gait & fall‑risk analyzer** · Engineering prototype · v0.1.0‑alpha  
*Research prototype. Not a medical device. Not FDA approved.*

---

## What this is
GaitIQ is a wearable AI system that collects IMU motion data from a prosthetic limb, detects terrain transitions, and estimates fall‑risk signals using explainable machine learning — with a live Streamlit dashboard for clinics and users.

---

## Problem
Above‑knee prosthesis users often experience instability during terrain changes (flat → slope → stairs). Clinics only see short hallway tests and rely on subjective feedback. There is no objective, real‑world data to support tuning.

---

## Solution (MVP)
A low‑cost IMU data logger + ML pipeline that:
- captures real‑world gait signals
- detects terrain transitions and instability events
- summarizes sessions into clear reports for prosthetists

---

## Project Phases (2‑Week Sprint)
**Phase 1 (Now): App + Data pipeline (no hardware)**
- Streamlit dashboard with CSV upload
- Synthetic data generator
- Feature extraction + baseline classifier

**Phase 2 (When hardware arrives):**
- ESP32‑S3 + BNO055 bring‑up
- CSV session logging
- Integrate real data into pipeline

**Phase 3+:**
- Improved terrain transition detection
- Fall‑risk model
- Explainability layer (SHAP)

---

## Repo Structure
```
gaitiq/
  firmware/
    phase1_bringup.ino
    phase2_stable_capture.ino
    phase3_wifi_stream.ino

  data/
    raw/
    processed/
    synthetic/
    generate_synthetic.py
    .gitkeep

  app/
    main.py
    pages/
      01_live_dashboard.py
      02_session_history.py
      03_gait_analysis.py
    components/
      risk_indicator.py
      gait_chart.py
      terrain_badge.py

  ml/
    features.py
    terrain_classifier.py
    fall_risk_model.py
    transition_detector.py
    models/

  receiver/
    socket_receiver.py
    session_logger.py

  docs/
    architecture.md
    wiring_diagram.md

  requirements.txt
  .gitignore
```

---

## Stack
- **Hardware:** ESP32‑S3 + Adafruit BNO055 IMU
- **Data:** CSV session logs
- **App:** Streamlit
- **ML:** scikit‑learn (baseline), SHAP (phase 3+)

---

## CSV Data Format (locked)
```
timestamp,ax,ay,az,gx,gy,gz,roll,pitch,yaw,terrain_label
1700000012,0.12,0.02,9.78,0.01,0.03,0.02,1.2,0.5,89.0,flat
```

---

## Quick Start (App)
```bash
pip install -r requirements.txt
streamlit run app/main.py
```

---

## Status
**Phase 1 — App + data pipeline in progress**

---

## Team Workflow
- **main** = stable only  
- **develop** = active work  
- **feature/GIQ-XXX** = one task per branch  
- Commit format: `type(scope): message [GIQ-XXX]`

**Types:** feat | fix | data | firmware | docs | refactor | test  
**Scopes:** app | ml | hw | data | docs  

---

## Notes
This is an engineering prototype intended for academic evaluation and research demonstration only.  
Not intended for medical use.
