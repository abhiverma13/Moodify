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
            scope="user-read-private user-read-email playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private",
        )

        # Check if there is a current token in the cache
        token_info = self.auth_manager.get_cached_token()

        if token_info and not self.auth_manager.is_token_expired(token_info):
            # Use the existing token if it's still valid
            self.auth_manager.token_info = token_info
        elif token_info and self.auth_manager.is_token_expired(token_info):
            # Refresh the token using the refresh token if it has expired
            self.auth_manager.refresh_access_token(token_info['refresh_token'])

        # Create a new Spotify client
        self.spotify_client = spotipy.Spotify(auth_manager=self.auth_manager)

    def get_user_profile(self):
      return self.spotify_client.current_user()

    def get_user_playlists(self):
      return self.spotify_client.current_user_playlists()
    
    def get_user_playlists_owned(self):
        # Get all playlists including collaborative playlists
        playlists = self.spotify_client.current_user_playlists()

        # Filter out playlists that are not owned by the user
        user_playlists_owned = [playlist for playlist in playlists['items'] if
                                playlist['owner']['id'] == self.spotify_client.current_user()['id'] or playlist['collaborative']]

        return user_playlists_owned

    def get_playlist_info(self, playlist_id):
        playlist_info = self.spotify_client.playlist(playlist_id)
        return playlist_info

    def get_playlist_tracks(self, playlist_id, limit, offset):
        tracks = self.spotify_client.playlist_tracks(playlist_id, limit=limit, offset=offset)
        return tracks
    
    def get_track_id(self, track_name, track_artist):
        results = self.spotify_client.search(q=f'{track_name} {track_artist}', type='track', limit=1)
        print("Seed Song: " + results['tracks']['items'][0]['name'] + " by " + results['tracks']['items'][0]['artists'][0]['name'])
        if results['tracks']['items']:
          track_id = results['tracks']['items'][0]['id']
          return track_id
        else:
          print(f'Track "{track_name}" not found.')

    def get_track_audio_features(self, track_id):
        return self.spotify_client.audio_features(track_id)
    
    def create_new_playlist(self, name, description, visibility='public'):
      user_info = self.spotify_client.current_user()
      username = user_info['id']
      playlist = self.spotify_client.user_playlist_create(user=username, name=name, public=(visibility.lower() == 'public'), description=description)

      return playlist['id']

    def add_tracks_to_playlist(self, playlist_id, tracks):
      track_ids = []

      # Iterate through the list of tracks and get their IDs
      for track in tracks:
          track_name, track_artist = track.split('-')
          track_id = self.get_track_id(track_name.strip(), track_artist.strip())
          if track_id:
              track_ids.append(track_id)

      # Add the tracks to the playlist
      user_info = self.spotify_client.current_user()
      username = user_info['id']
      self.spotify_client.user_playlist_add_tracks(username, playlist_id, track_ids)