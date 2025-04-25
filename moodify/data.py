"""Utilities to fetch tracks & engineer features ready for ML."""
from __future__ import annotations
import pandas as pd
from datetime import timedelta
from collections import Counter
from .client import MoodifySession

_FEATURE_COLUMNS = [  # 1‑to‑1 with Spotify audio features
    "acousticness", "danceability", "energy", "instrumentalness", "liveness",
    "loudness", "speechiness", "tempo", "valence", "duration_ms",
]

class DataBuilder:
    def __init__(self, session: MoodifySession):
        self.sess = session

    # ── Pull all tracks from a playlist & basic metadata ────────────────
    def playlist_df(self, playlist_uri: str) -> pd.DataFrame:
        rows = []
        for t in self.sess.playlist_tracks(playlist_uri):
            rows.append({
                "name": t["name"],
                "uri": t["uri"].split(":")[2],
                "artist": t["artists"][0]["name"],
            })
        return pd.DataFrame(rows)

    # ── Expand to audio features ────────────────────────────────────────
    def with_audio_features(self, df: pd.DataFrame) -> pd.DataFrame:
        feats = []
        for chunk in df["uri"].to_list():
            feats.extend(self.sess.audio_features([chunk]))
        feat_df = pd.DataFrame(feats)
        df = df.join(feat_df[_FEATURE_COLUMNS])
        df["duration"] = df["duration_ms"].apply(lambda ms: timedelta(milliseconds=ms))
        df.drop(columns=["duration_ms"], inplace=True)
        return df

    # ── Infer dominant genre from artist profile ────────────────────────
    def add_genre(self, df: pd.DataFrame) -> pd.DataFrame:
        import itertools, spotipy  # local import to keep top clean
        genres: list[list[str]] = []
        seen: dict[str, list[str]] = {}
        sp = spotipy.Spotify(auth_manager=self.sess._sp.auth_manager)
        for artist in df["artist"]:
            if artist in seen:
                genres.append(seen[artist])
                continue
            res = sp.search(artist, type="artist", limit=1)
            items = res["artists"]["items"]
            g = items[0]["genres"] if items else []
            seen[artist] = g
            genres.append(g)
        df["genres"] = genres
        # One main genre for convenience
        df["main_genre"] = df["genres"].apply(lambda gs: Counter(gs).most_common(1)[0][0] if gs else None)
        return df