# ml/fall_risk_model.py

import numpy as np


class FallRiskModel:
    def __init__(self):
        # Thresholds (tune later)
        self.symmetry_threshold = 0.75
        self.variance_threshold = 1.2
        self.cadence_low = 0.8
        self.cadence_high = 2.5

    # ----------------------------
    # Feature Computation
    # ----------------------------
    def compute_features(self, df):
        features = {}

        # Acceleration magnitude
        acc_mag = np.sqrt(df["ax"]**2 + df["ay"]**2 + df["az"]**2)

        features["mean_acc"] = acc_mag.mean()
        features["std_acc"] = acc_mag.std()

        # Simple cadence proxy
        features["cadence"] = self._estimate_cadence(acc_mag)

        # Symmetry proxy (left-right assumption simulated)
        features["symmetry"] = self._symmetry_index(acc_mag)

        return features

    # ----------------------------
    # Cadence Estimation
    # ----------------------------
    def _estimate_cadence(self, signal):
        peaks = (signal > signal.mean()).sum()
        duration = len(signal)

        return peaks / duration if duration > 0 else 0

    # ----------------------------
    # Symmetry Index (simple proxy)
    # ----------------------------
    def _symmetry_index(self, signal):
        mid = len(signal) // 2
        left = signal[:mid]
        right = signal[mid:]

        if len(left) == 0 or len(right) == 0:
            return 1.0

        return 1 - abs(left.mean() - right.mean()) / (left.mean() + 1e-6)

    # ----------------------------
    # Risk Prediction
    # ----------------------------
    def predict(self, features):
        symmetry = features["symmetry"]
        variance = features["std_acc"]
        cadence = features["cadence"]

        # Rule-based scoring
        risk_score = 0

        if symmetry < self.symmetry_threshold:
            risk_score += 2

        if variance > self.variance_threshold:
            risk_score += 2

        if cadence < self.cadence_low or cadence > self.cadence_high:
            risk_score += 1

        # Classification
        if risk_score >= 4:
            return "HIGH"
        elif risk_score >= 2:
            return "MEDIUM"
        else:
            return "LOW"