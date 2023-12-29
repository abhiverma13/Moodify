from spotifyclient import SpotifyClient
from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

spotify_client = SpotifyClient(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)

track1 = "Lonely"
track2 = "Young Girls"
track3 = "Without You"
track4 = "Set Fire to the Rain"
track5 = "Shower"
track6 = "OMG"

track_id_1 = spotify_client.get_track_id(track1)
track_id_2 = spotify_client.get_track_id(track2)
track_id_3 = spotify_client.get_track_id(track3)
track_id_4 = spotify_client.get_track_id(track4)
track_id_5 = spotify_client.get_track_id(track5)
track_id_6 = spotify_client.get_track_id(track6)


track_ids = [track_id_1, track_id_2, track_id_3, track_id_4, track_id_5, track_id_6]

audio_features = spotify_client.get_track_audio_features(track_ids)

i = 1
for feature in audio_features:
    print("Track Number", i)
    if feature['valence'] > 0.3:
        print("False")
    else:
        print("True")

    print("Valence:", feature['valence'])
    print("Danceability:", feature['danceability'])
    print("Energy:", feature['energy'])
    # Add more features as needed
    print("\n")
    i += 1