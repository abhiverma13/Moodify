from __future__ import annotations
from .client import MoodifySession
from .data import DataBuilder
from .model import MoodNet

class Curator:
    """High‑level utility you will call from notebooks or the CLI."""

    def __init__(self, sess: MoodifySession, model: MoodNet):
        self.sess = sess; self.model = model; self.builder = DataBuilder(sess)

    def mood_of_track(self, track_uri: str) -> str:
        df = self.builder.with_audio_features(
            self.builder.playlist_df({"items": [{"track": {"uri": track_uri}}]})  # hacky 1‑track df
        )
        return self.model.predict(df[_FEATURE_COLUMNS])[0]

    def curate_playlist(self, source_playlist: str, mood: str, *, new_name: str | None = None, public: bool = True):
        df = self.builder.with_audio_features(self.builder.playlist_df(source_playlist))
        df["pred"] = self.model.predict(df[_FEATURE_COLUMNS])
        keep_uris = df.loc[df["pred"] == mood, "uri"].tolist()
        dest_name = new_name or f"Moodify – {mood} mix"
        dest_id = self.sess.create_playlist(dest_name, f"Auto‑generated {mood} tracks", public=public)
        self.sess.add_tracks(dest_id, keep_uris)
        return dest_id, len(keep_uris)