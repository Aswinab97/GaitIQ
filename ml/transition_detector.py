# ml/transition_detector.py

import numpy as np


class TransitionDetector:
    def __init__(self, window_size=5):
        self.prev_class = None
        self.history = []
        self.window_size = window_size

    # ----------------------------
    # Update State
    # ----------------------------
    def update(self, current_class, confidence=None):
        transition = None

        if self.prev_class is not None and current_class != self.prev_class:
            transition = {
                "from": self.prev_class,
                "to": current_class,
                "confidence": confidence if confidence else 0.5
            }

        self.prev_class = current_class

        return transition

    # ----------------------------
    # Stability Check (optional)
    # ----------------------------
    def detect_instability(self, signal):
        self.history.append(np.std(signal))

        if len(self.history) > self.window_size:
            self.history.pop(0)

        if len(self.history) < self.window_size:
            return False

        # Detect sudden spike
        if self.history[-1] > np.mean(self.history[:-1]) * 1.5:
            return True

        return False