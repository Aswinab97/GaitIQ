import os
import glob
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

RAW_DIR = "data/raw"
MODEL_DIR = "ml/models"
os.makedirs(MODEL_DIR, exist_ok=True)

BASE_FEATURES = ["heading", "roll", "pitch", "ax", "ay", "az", "gx", "gy", "gz"]

def infer_label(fname):
    n = os.path.basename(fname).lower()
    labels = ["stairs_down","stairs_up","sit_to_stand","stand_to_sit","level_walk","standing","normal_walk","normal_walking"]
    for lb in labels:
        if lb in n:
            return "level_walk" if lb in ["normal_walk","normal_walking"] else lb
    return None

def load_data():
    files = sorted(glob.glob(os.path.join(RAW_DIR, "*.csv")))
    if not files:
        raise RuntimeError(f"No CSV found in {RAW_DIR}")

    dfs = []
    for f in files:
        df = pd.read_csv(f)

        for c in BASE_FEATURES:
            if c not in df.columns:
                df[c] = np.nan

        if "activity" in df.columns and df["activity"].notna().any():
            label = str(df["activity"].dropna().iloc[0]).strip().lower()
            if label in ["normal_walk", "normal_walking"]:
                label = "level_walk"
        else:
            label = infer_label(f)

        if label is None:
            print("Skip unknown:", os.path.basename(f))
            continue

        use = df[BASE_FEATURES].copy()
        for c in BASE_FEATURES:
            use[c] = pd.to_numeric(use[c], errors="coerce")
        use = use.dropna(how="all")
        use = use.fillna(0.0)

        use["label"] = label
        dfs.append(use)

    if not dfs:
        raise RuntimeError("No usable data.")
    return pd.concat(dfs, ignore_index=True)

def add_features(df, win=20):
    out = df.copy()
    for c in BASE_FEATURES:
        out[f"{c}_mean"] = out[c].rolling(win, min_periods=1).mean()
        out[f"{c}_std"] = out[c].rolling(win, min_periods=1).std().fillna(0)
    return out

def main():
    df = load_data()
    df = add_features(df, win=20)

    X_cols = [c for c in df.columns if c != "label"]
    X = df[X_cols].values
    y_text = df["label"].values

    le = LabelEncoder()
    y = le.fit_transform(y_text)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("rf", RandomForestClassifier(
            n_estimators=300,
            random_state=42,
            n_jobs=-1,
            class_weight="balanced_subsample"
        ))
    ])

    model.fit(X_train, y_train)
    pred = model.predict(X_test)

    print("\nClasses:", list(le.classes_))
    print("Accuracy:", round(accuracy_score(y_test, pred), 4))
    print("\nClassification report:\n", classification_report(y_test, pred, target_names=le.classes_))
    print("Confusion matrix:\n", confusion_matrix(y_test, pred))

    joblib.dump(model, os.path.join(MODEL_DIR, "terrain_rf_real.joblib"))
    joblib.dump(le, os.path.join(MODEL_DIR, "label_encoder_real.joblib"))
    joblib.dump(X_cols, os.path.join(MODEL_DIR, "feature_cols_real.joblib"))
    print("\nSaved models in:", MODEL_DIR)

if __name__ == "__main__":
    main()
