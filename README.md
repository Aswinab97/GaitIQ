# GaitIQ  
**Smart prosthetic gait & fall-risk analyzer · Engineering prototype · v0.1.0-alpha**

GaitIQ is an end-to-end prototype for:
- Collecting IMU gait data from ESP32 + BNO055
- Streaming live motion packets over UDP
- Running real-time gait inference in a Streamlit dashboard
- Training a classical ML model for terrain/activity classification

---

## 1) Quickstart (5 min)

### Prerequisites
- Python 3.11+ (recommended: 3.11/3.12)
- pip
- Git
- (Optional) ESP32 + BNO055 hardware for live streaming

### Setup
```bash
git clone https://github.com/Aswinab97/GaitIQ.git
cd GaitIQ

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### Run the app
```bash
python -m streamlit run app/main.py
```

Open the local URL shown in terminal (usually `http://localhost:8501`).

---

## 2) Train model from real data

Place labeled CSV session files in:
- `data/raw/`

Then run:
```bash
python ml/train_real_classifier.py
```

This generates model artifacts in:
- `ml/models/`

> Note: model binaries (`*.joblib`) are ignored by git by design.

---

## 3) Live UDP inference (ESP32)

1. Open app page: **Live UDP Inference**
2. Set:
   - UDP bind IP: `0.0.0.0`
   - UDP port: e.g. `4210`
3. Click **Start Live Inference**
4. Ensure ESP32 firmware sends UDP to your laptop IP + same port

Example receiver target in firmware:
```cpp
IPAddress receiverIP(192, 168, 2, 116);  // your laptop IP
const int receiverPort = 4210;
udp.beginPacket(receiverIP, receiverPort);
udp.print(payload);
udp.endPacket();
```

---

## 4) Project structure

```text
GaitIQ/
├── app/                  # Streamlit app
│   ├── main.py
│   ├── pages/
│   └── components/
├── ml/                   # Feature engineering + training scripts
│   └── models/           # Local model artifacts (gitignored)
├── firmware/             # ESP32 sketches
├── receiver/             # UDP/socket logging utilities
├── data/
│   ├── raw/              # Local raw sessions (gitignored)
│   ├── processed/
│   └── synthetic/
├── docs/
├── requirements.txt
└── Dockerfile
```

---

## 5) Reproducibility notes

- Use the same Python environment for training + inference.
- If model/scikit-learn versions differ, retrain model in current environment.
- Recommended run command:
```bash
python -m streamlit run app/main.py
```

---

## 6) Known limitations (v0.1.0-alpha)

- Single-user local prototype (not production deployment)
- Basic model validation only
- No cloud persistence/API yet
- Live UDP depends on local network stability and correct IP/port routing

---

## 7) Roadmap (next)

- Add CI (lint + tests)
- Add unit tests for feature pipeline and model loading
- Add confidence smoothing / majority vote in live inference
- Add experiment tracking and model report

---

## 8) License

MIT License — see [LICENSE](LICENSE).
