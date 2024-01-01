from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
import os
from spotifyclient import SpotifyClient

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

spotify_client = SpotifyClient(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)

app = Flask(__name__)

#HOME PAGE
@app.route("/")
def index():
    user_profile = spotify_client.get_user_profile()
    display_name = user_profile.get("display_name", "N/A")

    return render_template("index.html", display_name=display_name)


#EXISTING PLAYLIST
@app.route("/playlists", methods=['GET', 'POST'])
def playlists():
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
    try:
        playlist = spotify_client.get_playlist_info(playlist_id)
        return render_template('playlist_info.html', playlist=playlist)
    except Exception as e:
        user_profile = spotify_client.get_user_profile()
        display_name = user_profile.get("display_name", "N/A")
        return render_template('playlists.html', no_playlist_found=True, display_name=display_name)

@app.route("/playlist_info/<playlist_id>/<mood>")
def playlist_mood(playlist_id, mood):
    # Get the total number of tracks in the playlist
    playlist_info = spotify_client.get_playlist_info(playlist_id)
    total_tracks = playlist_info['tracks']['total']

    # Initialize a list to store tracks based on the specified mood
    mood_tracks = []

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

            # Check conditions for the specified mood
            if mood == 'Sad' and audio_features and all(
                feature['valence'] < 0.3 and feature['energy'] < 0.6 and feature['danceability'] < 0.8
                for feature in audio_features
            ):
                print("True")
                mood_tracks.append(track["track"])
            elif mood == 'Party' and audio_features and all(
                (feature['energy'] + feature['danceability'])/2 > 0.65 and (feature['danceability'] > 0.7 or feature['energy'] > 0.7) and feature['tempo'] > 120
                for feature in audio_features
            ):
                print("True")
                mood_tracks.append(track["track"])
            else:
                print("False")
            j += 1

    playlist_name = playlist_info['name']
    playlist_id = playlist_info['id']

    return render_template("playlist_mood.html", playlist_name=playlist_name, playlist_id=playlist_id, mood=mood, tracks=mood_tracks)

@app.route("/add_to_existing_playlist", methods=['GET', 'POST'])
def add_to_existing_playlist():
    selected_tracks = request.args.getlist('selected_tracks')
    playlists_owned = spotify_client.get_user_playlists_owned()
    playlist_data = [{'name': playlist['name'], 'id': playlist['id']} for playlist in playlists_owned]

    if request.method == 'POST':
      playlist_id = request.form.get('playlist_id')
      if playlist_id:
          try:
            spotify_client.add_tracks_to_playlist(playlist_id, selected_tracks)
            return redirect(url_for('added_to_playlist', playlist_id=playlist_id))
          except Exception as e:
            return render_template('add_to_existing_playlist.html', no_playlist_found=True)

    return render_template('add_to_existing_playlist.html', playlists=playlist_data, selected_tracks=selected_tracks)

@app.route("/added_to_playlist/<playlist_id>")
def added_to_playlist(playlist_id):
    
    playlist = spotify_client.get_playlist_info(playlist_id)
    return render_template('added_to_playlist.html', playlist=playlist)

@app.route("/create_playlist", methods=['GET', 'POST'])
def create_playlist():
    selected_tracks = request.args.getlist('selected_tracks')
    print(selected_tracks)

    if request.method == 'POST':
        # Get the form data
        playlist_name = request.form.get('playlist_name')
        playlist_description = request.form.get('playlist_description')
        playlist_visibility = request.form.get('playlist_visibility')

        # Create the new playlist
        playlist_id = spotify_client.create_new_playlist(playlist_name, playlist_description, playlist_visibility)

        # Add tracks to the new playlist
        if playlist_id and selected_tracks:
            spotify_client.add_tracks_to_playlist(playlist_id, selected_tracks)

        # Redirect to the playlist created path
        return redirect(url_for('playlist_created', playlist_id=playlist_id))

    # Render the page to enter playlist details and display selected tracks
    return render_template('create_playlist.html', selected_tracks=selected_tracks)

@app.route("/playlist_created/<playlist_id>")
def playlist_created(playlist_id):
    
    playlist_info = spotify_client.get_playlist_info(playlist_id)
    return render_template('playlist_created.html', playlist=playlist_info)


#FIND SIMILAR SONGS
@app.route("/enter_seeds", methods=['GET', 'POST'])
def enter_seeds():
    if request.method == 'POST':
        # Retrieve form data for each seed song
        seed_song_ids = []
        seed_songs = []
        for i in range(1, 6):  # Assuming you have five seed song inputs
            song_key = f"song{i}"
            artist_key = f"artist{i}"
            song_name = request.form.get(song_key)
            if not song_name:
                continue
            artist_name = request.form.get(artist_key)
            try:
                song_id = spotify_client.get_track_id(song_name, artist_name)
                if song_id:
                    seed_song_ids.append(song_id)
                    seed_songs.append({'name': song_name, 'artist': artist_name})
            except Exception as e:
                return render_template("enter_seeds.html", error=True)
            
        num_similar_songs = int(request.form.get('num_songs'))
        
        return redirect(url_for('similar_songs_found', seed_song_ids=seed_song_ids, num_similar_songs=num_similar_songs))

    return render_template("enter_seeds.html")

@app.route("/similar_songs_found")
def similar_songs_found():
    num_similar_songs = request.args.get('num_similar_songs')
    seed_song_ids = request.args.getlist('seed_song_ids')

    similar_songs = spotify_client.get_similar_songs(seed_song_ids, num_similar_songs)
    similar_songs = [{'name': song['name'], 'artist': song['artists'][0]['name']} for song in similar_songs['tracks']]
    return render_template("similar_songs_found.html", similar_songs=similar_songs)

if __name__ == "__main__":
    app.run(debug=True)