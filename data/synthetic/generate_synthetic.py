from pathlib import Path
import numpy as np
import pandas as pd

np.random.seed(42)

def make_segment(n, terrain, t0):
    t = np.arange(n) / 100.0 + t0  # 100 Hz
    # base signals
    ax = 0.2 * np.sin(2 * np.pi * 1.6 * t) + np.random.normal(0, 0.03, n)
    ay = 0.1 * np.sin(2 * np.pi * 1.2 * t + 0.5) + np.random.normal(0, 0.03, n)
    az = 9.81 + 0.4 * np.sin(2 * np.pi * 1.6 * t + 1.0) + np.random.normal(0, 0.05, n)

    gx = 0.05 * np.sin(2 * np.pi * 1.6 * t) + np.random.normal(0, 0.01, n)
    gy = 0.06 * np.sin(2 * np.pi * 1.4 * t) + np.random.normal(0, 0.01, n)
    gz = 0.04 * np.sin(2 * np.pi * 1.5 * t) + np.random.normal(0, 0.01, n)

    roll = 2.0 * np.sin(2 * np.pi * 0.6 * t) + np.random.normal(0, 0.2, n)
    pitch = 3.0 * np.sin(2 * np.pi * 0.5 * t) + np.random.normal(0, 0.2, n)
    yaw = 90 + 4.0 * np.sin(2 * np.pi * 0.2 * t) + np.random.normal(0, 0.3, n)

    # terrain-specific adjustments
    if terrain == "stairs":
        az += 0.35 * np.sin(2 * np.pi * 2.3 * t)
        pitch += 4.0
    elif terrain == "slope":
        pitch += 7.0
        roll += 1.5
    elif terrain == "unstable":
        ax += np.random.normal(0, 0.12, n)
        ay += np.random.normal(0, 0.12, n)
        gx += np.random.normal(0, 0.05, n)
        gy += np.random.normal(0, 0.05, n)

    return pd.DataFrame({
        "timestamp": (t * 1000).astype(np.int64),  # ms
        "ax": ax, "ay": ay, "az": az,
        "gx": gx, "gy": gy, "gz": gz,
        "roll": roll, "pitch": pitch, "yaw": yaw,
        "terrain_label": terrain
    })

def main():
    out_dir = Path("data/synthetic")
    out_dir.mkdir(parents=True, exist_ok=True)

    segments = []
    t0 = 0.0
    plan = [("flat", 1200), ("stairs", 900), ("flat", 900), ("slope", 900), ("unstable", 600)]
    for terrain, n in plan:
        seg = make_segment(n, terrain, t0)
        segments.append(seg)
        t0 = seg["timestamp"].iloc[-1] / 1000.0 + 0.01

    df = pd.concat(segments, ignore_index=True)
    out_file = out_dir / "session_synthetic_v1.csv"
    df.to_csv(out_file, index=False)
    print(f"Saved: {out_file} | rows={len(df)}")

if __name__ == "__main__":
    main()