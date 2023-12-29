import spotipy
from spotipy.oauth2 import SpotifyOAuth

class SpotifyClient:
    def __init__(self, client_id, client_secret, redirect_uri):
      self.client_id = client_id
      self.client_secret = client_secret
      self.redirect_uri = redirect_uri
      self.auth_manager = SpotifyOAuth(
        client_id,
        client_secret,
        redirect_uri,
        scope="user-read-private user-read-email playlist-read-private playlist-read-collaborative",
      )
      self.spotify_client = spotipy.Spotify(auth_manager=self.auth_manager)

    def get_user_profile(self):
      return self.spotify_client.current_user()

    def get_user_playlists(self):
      return self.spotify_client.current_user_playlists()

    def get_playlist_info(self, playlist_id):
        playlist_info = self.spotify_client.playlist(playlist_id)
        return playlist_info

    def get_playlist_tracks(self, playlist_id, limit, offset):
        tracks = self.spotify_client.playlist_tracks(playlist_id, limit=limit, offset=offset)
        return tracks
    
    def get_track_id(self, track_name):
        results = self.spotify_client.search(q=track_name, type='track', limit=1)
        print("Seed Song: " + results['tracks']['items'][0]['name'] + " by " + results['tracks']['items'][0]['artists'][0]['name'])
        if results['tracks']['items']:
          track_id = results['tracks']['items'][0]['id']
          return track_id
        else:
          print(f'Track "{track_name}" not found.')

    def get_track_audio_features(self, track_id):
        return self.spotify_client.audio_features(track_id)
  