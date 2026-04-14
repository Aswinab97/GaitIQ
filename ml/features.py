import numpy as np
import pandas as pd

WINDOW = 100  # 1 second at 100Hz
STEP = 50     # 50% overlap

FEATURE_COLS = [
    "ax_mean","ay_mean","az_mean",
    "ax_std","ay_std","az_std",
    "gx_std","gy_std","gz_std",
    "roll_mean","pitch_mean",
    "acc_mag_mean","acc_mag_std",
    "cadence_hz"
]

def estimate_cadence_hz(az_window: np.ndarray, fs: float = 100.0) -> float:
    x = az_window - np.mean(az_window)
    # simple peak count using sign changes in derivative
    dx = np.diff(x)
    peaks = np.where((np.hstack([dx, 0.0]) <= 0) & (np.hstack([0.0, dx]) > 0))[0]
    # crude threshold to reject noise peaks
    peaks = peaks[x[peaks] > np.std(x) * 0.3]
    duration_s = len(az_window) / fs
    if duration_s <= 0:
        return 0.0
    return len(peaks) / duration_s

def compute_window_features(win: pd.DataFrame) -> dict:
    acc_mag = np.sqrt(win["ax"]**2 + win["ay"]**2 + win["az"]**2)

    feats = {
        "ax_mean": win["ax"].mean(),
        "ay_mean": win["ay"].mean(),
        "az_mean": win["az"].mean(),
        "ax_std": win["ax"].std(),
        "ay_std": win["ay"].std(),
        "az_std": win["az"].std(),
        "gx_std": win["gx"].std(),
        "gy_std": win["gy"].std(),
        "gz_std": win["gz"].std(),
        "roll_mean": win["roll"].mean(),
        "pitch_mean": win["pitch"].mean(),
        "acc_mag_mean": acc_mag.mean(),
        "acc_mag_std": acc_mag.std(),
        "cadence_hz": estimate_cadence_hz(win["az"].values, fs=100.0),
    }
    return feats

def extract_features(df: pd.DataFrame, window: int = WINDOW, step: int = STEP) -> pd.DataFrame:
    required = ["timestamp","ax","ay","az","gx","gy","gz","roll","pitch","yaw","terrain_label"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    rows = []
    n = len(df)

    for start in range(0, n - window + 1, step):
        end = start + window
        win = df.iloc[start:end]
        feats = compute_window_features(win)
        feats["terrain_label"] = win["terrain_label"].mode().iloc[0]
        feats["t_start"] = win["timestamp"].iloc[0]
        feats["t_end"] = win["timestamp"].iloc[-1]
        rows.append(feats)

    return pd.DataFrame(rows)

if __name__ == "__main__":
    # quick local test
    test_path = "data/synthetic/session_synthetic_v1.csv"
    data = pd.read_csv(test_path)
    out = extract_features(data)
    out_path = "data/processed/features_session_synthetic_v1.csv"
    out.to_csv(out_path, index=False)
    print(f"Saved features: {out_path} | rows={len(out)} | cols={len(out.columns)}")