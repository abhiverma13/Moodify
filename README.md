# Spotify-Playlist-Generator

This Flask web application interacts with the Spotify API to perform various tasks related to your playlists, including finding new song recommendations and finding the existing songs in your playlists according to your mood.

## Getting Started

Follow these steps to set up the application and obtain the required credentials:

### 1. Create a Spotify Developer Account

Visit the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/) and log in or create a new account.

### 2. Create a New App

- Click on the "Create an App" button.
- Fill in the required information for your new app.
- For the Redirect URI you can use `http://localhost:5000/callback`.
- Accept the terms and conditions.

### 3. Obtain CLIENT_ID, CLIENT_SECRET and REDIRECT_URI

- Once your app is created, go to the app's dashboard.
- Note down the `CLIENT_ID`, `CLIENT_SECRET` and `REDIRECT_URI` from the app settings.

### 5. Save Credentials in .env File

Create a `.env` file in the project's root directory and add the following lines:

```plaintext
CLIENT_ID=<your_client_id>
CLIENT_SECRET=<your_client_secret>
REDIRECT_URI=<your_redirect_uri>
```
## Running the App

### 1. Install Dependencies Using Terminal

```bash
pip install -r requirements.txt
```
### 2. Run the Flask App Using Terminal
```bash
python app.py
```
### 3. Access the App
Open your web browser and go to http://localhost:5000/ to access the app.