"""Handles PKCE OAuth2 flow & token caching – no secrets hard‑coded."""
from __future__ import annotations
import os, pathlib
from spotipy.oauth2 import SpotifyOAuth

_SCOPES = (
    "playlist-modify-private playlist-modify-public "
    "playlist-read-private playlist-read-collaborative user-read-private"
)
_CACHE = pathlib.Path.home() / ".cache-moodify"

class CredentialStore:
    """Thin wrapper so the rest of the code never touches SpotifyOAuth."""

    def __init__(self, *, client_id: str | None = None, client_secret: str | None = None, redirect_uri: str | None = None):
        self.oauth = SpotifyOAuth(
            client_id=client_id or os.getenv("CLIENT_ID"),
            client_secret=client_secret or os.getenv("CLIENT_SECRET"),
            redirect_uri=redirect_uri or os.getenv("REDIRECT_URI", "http://localhost:8888/callback"),
            scope=_SCOPES,
            cache_path=_CACHE,
            open_browser=True,
            show_dialog=False,
        )

    def token(self) -> str:
        token_info = self.oauth.get_cached_token()
        if token_info and not self.oauth.is_token_expired(token_info):
            return token_info["access_token"]
        if token_info and self.oauth.is_token_expired(token_info):
            token_info = self.oauth.refresh_access_token(token_info["refresh_token"])
            return token_info["access_token"]
        # first‑time auth – opens browser
        return self.oauth.get_access_token()["access_token"]