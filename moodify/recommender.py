from __future__ import annotations
import pathlib
import pandas as pd

from .client import MoodifySession
from .data import DataBuilder
from .model import MoodNet

_FEATURE_COLUMNS = [  # mirror Spotify audio‑feature keys used in model
    "acousticness",
    "danceability",
    "energy",
    "instrumentalness",
    "liveness",
    "loudness",
    "speechiness",
    "tempo",
    "valence",
]


class Curator:
    """High‑level helper that glues *MoodifySession* + *MoodNet* together.

    Parameters
    ----------
    sess : MoodifySession
        Authenticated Spotify wrapper (light façade over Spotipy).
    model : MoodNet
        Trained neural network loaded via :py:meth:`MoodNet.load`.
    """

    def __init__(self, sess: MoodifySession, model: MoodNet):
        self.sess = sess
        self.model = model
        self.builder = DataBuilder(sess)

    # ------------------------------------------------------------------
    # single‑track helper (rarely used but good for demos) -------------
    # ------------------------------------------------------------------

    def mood_of_track(self, track_uri: str) -> str:
        """Return the predicted mood of an individual track URI."""
        tmp_df = self.builder.with_audio_features(
            self.builder.playlist_df({"items": [{"track": {"uri": track_uri}}]})
        )
        return self.model.predict(tmp_df[_FEATURE_COLUMNS])[0]

    # ------------------------------------------------------------------
    # main entry‑point --------------------------------------------------
    # ------------------------------------------------------------------

    def curate_playlist(
        self,
        target_mood: str,
        *,
        source_playlist: str | None = None,
        prebuilt_csv: pathlib.Path | None = None,
        new_name: str | None = None,
        public: bool = True,
    ):
        """Filter *either* a live playlist **or** a pre‑existing CSV.

        Exactly one of *source_playlist* **or** *prebuilt_csv* must be
        provided:

        * **Live playlist path**  – Fetch tracks via Spotify → predict moods.
        * **CSV path**            – Load rows already containing the required
          audio‑feature columns.
        """
        if bool(source_playlist) == bool(prebuilt_csv):
            raise ValueError("Pass *either* source_playlist or prebuilt_csv, not both.")

        # 1) Build the feature DataFrame --------------------------------
        if source_playlist:
            df = self.builder.with_audio_features(self.builder.playlist_df(source_playlist))
        else:
            df = pd.read_csv(prebuilt_csv)
            missing = set(_FEATURE_COLUMNS) - set(df.columns)
            if missing:
                raise ValueError(f"CSV missing feature columns: {', '.join(missing)}")

        # 2) Predict & filter ------------------------------------------
        df["pred"] = self.model.predict(df[_FEATURE_COLUMNS])
        # case‑fold both sides so "sad" == "Sad" etc.
        target_norm = target_mood.lower().strip()
        df["pred_norm"] = df["pred"].str.lower().str.strip()
        keep_uris = df.loc[df["pred_norm"] == target_norm, "uri"].tolist()

        # 3) Create destination playlist -------------------------------
        dest_name = new_name or f"Moodify – {target_mood} mix"
        dest_id = self.sess.create_playlist(
            dest_name,
            f"Auto‑generated {target_mood} tracks",
            public=public,
        )
        self.sess.add_tracks(dest_id, keep_uris)
        return dest_id, len(keep_uris)