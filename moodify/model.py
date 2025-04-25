"""Train & persist the neural network described in the original project."""
from __future__ import annotations
import json, pathlib, joblib
import numpy as np, pandas as pd
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

class MoodNet:
    def __init__(self):
        self.scaler = MinMaxScaler()
        self.encoder = LabelEncoder()
        self.model = None

    def _build_keras(self, input_dim: int, output_dim: int):
        m = Sequential([
            Dense(64, activation="relu", input_dim=input_dim),
            Dense(32, activation="relu"),
            Dense(output_dim, activation="softmax"),
        ])
        m.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
        return m

    def fit(self, df: pd.DataFrame, *, label_col: str = "mood", epochs: int = 25):
        X = self.scaler.fit_transform(df.drop(columns=[label_col]))
        y = self.encoder.fit_transform(df[label_col])
        X_tr, X_val, y_tr, y_val = train_test_split(X, y, test_size=0.2, stratify=y)
        self.model = self._build_keras(X.shape[1], len(self.encoder.classes_))
        self.model.fit(X_tr, y_tr, validation_data=(X_val, y_val), epochs=epochs, verbose=2)
        print(classification_report(y_val, np.argmax(self.model.predict(X_val), axis=1)))
        return self

    # ─── Persistence ────────────────────────────────────────────────────
    def save(self, path: str | pathlib.Path):
        path = pathlib.Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.model.save(path)
        joblib.dump({
            "scaler": self.scaler,
            "encoder": self.encoder,
        }, path.with_suffix(".meta"))

    @classmethod
    def load(cls, path: str | pathlib.Path):
        import tensorflow as tf
        obj = cls()
        obj.model = tf.keras.models.load_model(path)
        meta = joblib.load(path.with_suffix(".meta"))
        obj.scaler = meta["scaler"]; obj.encoder = meta["encoder"]
        return obj

    # ─── Prediction helpers ─────────────────────────────────────────────
    def predict(self, features: pd.DataFrame):
        X = self.scaler.transform(features)
        preds = np.argmax(self.model.predict(X, verbose=0), axis=1)
        return self.encoder.inverse_transform(preds)