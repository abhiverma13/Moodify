from __future__ import annotations
import pathlib, joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input


class MoodNet:
    """Neural‑net wrapper that handles scaling, label‑encoding, training, and
    persistence in one place.

    Attributes
    ----------
    scaler : MinMaxScaler
        Rescales each numeric feature into [0,1] so the network trains fast.
    encoder : LabelEncoder
        Maps string mood labels ("Happy", "Sad", …) → integers 0‑N.
    model : tensorflow.keras.Model | None
        The compiled Keras Sequential network (set after :py:meth:`fit`).
    """

    def __init__(self):
        self.scaler = MinMaxScaler()
        self.encoder = LabelEncoder()
        self.model = None
        self._train_metrics: dict[str, float] = {}

    # ------------------------------------------------------------------
    # Network builder
    # ------------------------------------------------------------------

    @staticmethod
    def _build_keras(input_dim: int, output_dim: int):
        model = Sequential([
            Input(shape=(input_dim,)),
            Dense(64, activation="relu"),
            Dense(32, activation="relu"),
            Dense(output_dim, activation="softmax"),
        ])
        model.compile(
            optimizer="adam",
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )
        return model               # ← return the compiled model, *not* compile()


    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def fit(self, df: pd.DataFrame, *, label_col: str = "mood", epochs: int = 25):
        """Fit the network and print both *training* and *validation* scores."""
        X = df.drop(columns=[label_col]).select_dtypes(include=["number"])
        
        y = self.encoder.fit_transform(df[label_col])
        X = self.scaler.fit_transform(X)

        X_tr, X_val, y_tr, y_val = train_test_split(
            X, y, test_size=0.20, stratify=y
        )

        self.model = self._build_keras(X.shape[1], len(self.encoder.classes_))
        self.model.fit(
            X_tr,
            y_tr,
            validation_data=(X_val, y_val),
            epochs=epochs,
            verbose=2,
        )

        # ---------------- Evaluation ----------------
        y_tr_pred = np.argmax(self.model.predict(X_tr, verbose=0), axis=1)
        y_val_pred = np.argmax(self.model.predict(X_val, verbose=0), axis=1)

        train_acc = accuracy_score(y_tr, y_tr_pred)
        val_acc = accuracy_score(y_val, y_val_pred)
        self._train_metrics = {"train_acc": train_acc, "val_acc": val_acc}

        print("\n── Training set report ──")
        print(classification_report(y_tr, y_tr_pred, target_names=self.encoder.classes_))
        print("── Validation set report ──")
        print(classification_report(y_val, y_val_pred, target_names=self.encoder.classes_))

        return self

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def save(self, path: str | pathlib.Path):
        """Save **model**, **scaler**, and **encoder** next to each other."""
        path = pathlib.Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.model.save(path.with_suffix(".keras"))
        joblib.dump({"scaler": self.scaler, "encoder": self.encoder}, path.with_suffix(".meta"))

    @classmethod
    def load(cls, path: str | pathlib.Path):
        from tensorflow.keras.models import load_model

        instance = cls()
        instance.model = load_model(path)
        meta = joblib.load(path.with_suffix(".meta"))
        instance.scaler = meta["scaler"]
        instance.encoder = meta["encoder"]
        return instance

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict(self, features: pd.DataFrame | np.ndarray):
        """Return the **string** mood prediction for each row in *features*."""
        X = (
            self.scaler.transform(features)
            if isinstance(features, pd.DataFrame)
            else self.scaler.transform(np.asarray(features))
        )
        preds = np.argmax(self.model.predict(X, verbose=0), axis=1)
        return self.encoder.inverse_transform(preds)

    # ------------------------------------------------------------------
    # Convenience getters
    # ------------------------------------------------------------------

    @property
    def train_accuracy(self) -> float | None:
        return self._train_metrics.get("train_acc")

    @property
    def val_accuracy(self) -> float | None:
        return self._train_metrics.get("val_acc")