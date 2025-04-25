"""User‑level Spotify operations – renamed from SpotifyClient."""
from __future__ import annotations
import spotipy
from .auth import CredentialStore

class MoodifySession:
    """A very small façade so the rest of the app never sees Spotipy."""

    def __init__(self, store: CredentialStore | None = None):
        self._sp = spotipy.Spotify(auth=store.token())

    # ─── User Info ──────────────────────────────────────────────────────────
    def profile(self):
        return self._sp.current_user()

    def playlists(self, *, owned_only: bool = False):
        pls = self._sp.current_user_playlists()["items"]
        if not owned_only:
            return pls
        uid = self.profile()["id"]
        return [p for p in pls if p["owner"]["id"] == uid or p["collaborative"]]

    # ─── Tracks & features ─────────────────────────────────────────────────
    def playlist_tracks(self, playlist_id: str, *, batch: int = 100):
        offset, total = 0, 1
        while offset < total:
            chunk = self._sp.playlist_tracks(playlist_id, limit=batch, offset=offset)
            total = chunk["total"]
            for item in chunk["items"]:
                yield item["track"]
            offset += batch

    def audio_features(self, track_ids: list[str]):
        return self._sp.audio_features(track_ids)

    # ─── Playlist authoring ────────────────────────────────────────────────
    def create_playlist(self, name: str, description: str = "", *, public: bool = False) -> str:
        uid = self.profile()["id"]
        pl = self._sp.user_playlist_create(uid, name, public=public, description=description)
        return pl["id"]

    def add_tracks(self, playlist_id: str, track_ids: list[str]):
        # Spotify caps at 100 tracks per request
        for i in range(0, len(track_ids), 100):
            self._sp.playlist_add_items(playlist_id, track_ids[i : i + 100])