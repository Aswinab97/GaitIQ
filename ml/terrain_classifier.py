import joblib
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.model_selection import train_test_split

FEATURES_PATH = "data/processed/features_session_synthetic_v1.csv"
MODEL_PATH = "ml/models/terrain_rf.joblib"

FEATURE_COLS = [
    "ax_mean","ay_mean","az_mean",
    "ax_std","ay_std","az_std",
    "gx_std","gy_std","gz_std",
    "roll_mean","pitch_mean",
    "acc_mag_mean","acc_mag_std",
    "cadence_hz"
]

def main():
    df = pd.read_csv(FEATURES_PATH)

    X = df[FEATURE_COLS]
    y = df["terrain_label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced"
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)

    print("\n=== Terrain Classifier Results ===")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    Path("ml/models").mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, MODEL_PATH)
    print(f"\nSaved model: {MODEL_PATH}")

if __name__ == "__main__":
    main()