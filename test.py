from spotifyclient import SpotifyClient
from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

spotify_client = SpotifyClient(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)

track1 = "Feels"
artist1 = "Tory Lanez"
track2 = "Face Down"
artist2 = "Vedo"
track3 = "B.E.D."
artist3 = "Jacquees"
track4 = "Candy"
artist4 = "Doja Cat"
track5 = "Entertainer"
artist5 = "ZAYN"
track6 = "Woman's Worth"
artist6 = "Jacquees"

track_id_1 = spotify_client.get_track_id(track1, artist1)
track_id_2 = spotify_client.get_track_id(track2, artist2)
track_id_3 = spotify_client.get_track_id(track3, artist3)
track_id_4 = spotify_client.get_track_id(track4, artist4)
track_id_5 = spotify_client.get_track_id(track5, artist5)
track_id_6 = spotify_client.get_track_id(track6, artist6)


track_ids = [track_id_1, track_id_2, track_id_3, track_id_4, track_id_5, track_id_6]

audio_features = spotify_client.get_track_audio_features(track_ids)

i = 1
for feature in audio_features:
    print("Track Number", i)
    print("Tempo:", feature['tempo'])
    print("Danceability:", feature['danceability'])
    print("Energy:", feature['energy'])
    # Add more features as needed
    print("\n")
    i += 1