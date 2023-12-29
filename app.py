from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
import os
from spotifyclient import SpotifyClient

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

app = Flask(__name__)

#HOME PAGE
@app.route("/")
def index():
    spotify_client = SpotifyClient(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)

    user_profile = spotify_client.get_user_profile()
    display_name = user_profile.get("display_name", "N/A")

    return render_template("index.html", display_name=display_name)


#EXISTING PLAYLIST
@app.route("/playlists", methods=['GET', 'POST'])
def playlists():
    spotify_client = SpotifyClient(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)

    user_profile = spotify_client.get_user_profile()
    display_name = user_profile.get("display_name", "N/A")

    if request.method == 'POST':
      playlist_id = request.form.get('playlist_id')
      if playlist_id:
          return redirect(url_for('playlist_info', playlist_id=playlist_id))

    playlists = spotify_client.get_user_playlists()
    playlist_data = [{'name': playlist['name'], 'id': playlist['id']} for playlist in playlists['items']]

    return render_template("playlists.html", display_name=display_name, playlists=playlist_data)

@app.route("/playlist_info/<playlist_id>")
def playlist_info(playlist_id):
    spotify_client = SpotifyClient(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)

    try:
        playlist = spotify_client.get_playlist_info(playlist_id)
        return render_template('playlist_info.html', playlist=playlist)
    except Exception as e:
        user_profile = spotify_client.get_user_profile()
        display_name = user_profile.get("display_name", "N/A")
        return render_template('playlists.html', no_playlist_found=True, display_name=display_name)

# Updated route for handling "Sad" mood
@app.route("/playlist_info/<playlist_id>/sad")
def playlist_sad(playlist_id):
    spotify_client = SpotifyClient(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)

    # Get the total number of tracks in the playlist
    playlist_info = spotify_client.get_playlist_info(playlist_id)
    total_tracks = playlist_info['tracks']['total']

    # Initialize a list to store sad tracks
    sad_tracks = []

    # Set the maximum number of tracks to retrieve per request
    limit = 50  # You can adjust this value based on your needs

    # Calculate the number of requests needed based on the total number of tracks
    num_requests = -(-total_tracks // limit)  # Ceiling division to get the number of requests
    
    j = 1
    # Iterate through each request
    for i in range(num_requests):
        # Calculate the offset for the current request
        offset = i * limit

        # Get tracks in the playlist with the current offset
        playlist_tracks = spotify_client.get_playlist_tracks(playlist_id, limit, offset)
        # Iterate through each track in the current request
        for track in playlist_tracks["items"]:
            print("Track " + str(j))
            print(track["track"]["name"])
            track_id = track["track"]["id"]

            # Get audio features for the track
            audio_features = spotify_client.get_track_audio_features(track_id)

            # Check conditions for a "sad" track
            if audio_features and all(
                feature['valence'] < 0.3 and feature['energy'] < 0.6 and feature['danceability'] < 0.8
                for feature in audio_features
            ):
                print("True")
                sad_tracks.append(track["track"])
            else:
                print("False")
            j += 1

    playlist_name = playlist_info['name']
    playlist_id = playlist_info['id']

    return render_template("playlist_mood.html", playlist_name=playlist_name, playlist_id=playlist_id, mood="Sad", tracks=sad_tracks)


#NEW PLAYLIST
@app.route("/enter_seeds")
def enter_seeds():
    return render_template("enter_seeds.html")

if __name__ == "__main__":
    app.run(debug=True)