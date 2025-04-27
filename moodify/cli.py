import pathlib
import typer
import pandas as pd
from typing import List

from moodify.auth import CredentialStore
from moodify.client import MoodifySession
from moodify.data import DataBuilder
from moodify.model import MoodNet
from moodify.recommender import Curator

app = typer.Typer(help="🎧Moodify – mood‑based playlists")

def get_session() -> MoodifySession:
    """Return an authenticated Spotify session created lazily per command."""
    return MoodifySession(CredentialStore())

@app.command(help="List your Spotify playlists. Add --mine to show only those you own.")
def playlists(
    owned_only: bool = typer.Option(False, "--mine", help="Only show playlists you own"),
):
    """Print each playlist's *name* and *URI*."""
    sess = get_session()
    for p in sess.playlists(owned_only=owned_only):
        typer.echo(f"{p['name']} → {p['uri']}")

@app.command(
    help="Build a labelled CSV by harvesting tracks from playlists whose titles contain the given mood words (Recommended: Happy, Sad, Energetic, or Calm)."
)
def build_dataset(
    moods: List[str] = typer.Argument(..., metavar="MOODS", help="One or more mood words"),
    out: pathlib.Path = typer.Option("data/train.csv", help="Destination CSV file (default: dataset/train.csv)"),
    add_genres: bool = typer.Option(
        False, "--genres", help="Include artist genre columns"
    ),
):
    """Build a labelled CSV of audio‑feature rows.

    **What it does**
    1. Scans *every* playlist in your library.
    2. If the playlist title contains **any** of the given *moods* (case‑insensitive),
       every track inside that playlist is harvested.
    3. For each harvested track we call the Spotify *audio‑features* endpoint and
       append the 10 numerical columns (danceability, energy, valence, etc.).
    4. Adds a `mood` column whose value is the matching mood word.
    5. Concatenates rows from all matching playlists and writes them to *--out*.

    **Arguments**
    ▸ *MOODS* – one or more mood keywords (space‑separated). Example:
      `moodify build-dataset Happy Sad Chill`.

    **Options**
    ▸ `--out PATH` – where to save the CSV (default: `dataset.csv`).
    ▸ `--genres` – add a column with the artist's genre (optional).

    Example
    -------
    ```bash
    moodify build-dataset Happy Sad --out data/moods.csv
    ```
    """
    sess = get_session()
    builder = DataBuilder(sess)

    frames = []
    for m in moods:
        for pl in sess.playlists():
            if m.lower() in pl["name"].lower():
                df = builder.with_audio_features(builder.playlist_df(pl["uri"]))
                if add_genres:
                    df = builder.add_genre(df) # Optional: full list of Spotify genres for the track’s primary artist
                df["mood"] = m.title()
                frames.append(df)

    if not frames:
        typer.echo("⚠️  No matching playlists found.", err=True)
        raise typer.Exit(code=1)

    pd.concat(frames).to_csv(out, index=False)
    typer.echo(f"Saved {sum(len(f) for f in frames)} rows → {out}")

@app.command(help="Train the MoodNet neural network on a CSV and save the weights.")
def train(
    csv: pathlib.Path = typer.Argument(..., metavar="CSV", help="Path to the training CSV"),
    epochs: int = typer.Option(25, help="Number of training epochs (default: 25)"),
    save: pathlib.Path = typer.Option("model/moodnet.keras", help="Where to store model weights & metadata"),
):
    """Train **MoodNet** on a labelled CSV and persist the resulting model.

    **What it does**
    1. **Load & validate data** – reads the CSV (created by `build-dataset`) into
       a DataFrame. All numeric columns ('danceability', 'energy', etc.) become
       features; the `mood` column is the target label.
    2. **Pre‑processing** – inside `MoodNet.fit` the features are scaled to 0‑1
       with *MinMaxScaler* and the string labels are turned into class integers
       with *LabelEncoder*.
    3. **Train/validation split** – `train_test_split(test_size=0.2, stratify=y)`
       creates an 80‑% training set and a 20‑% validation set so accuracy & F1
       are measured on unseen data.
    4. **Neural‑net training** – a Keras Sequential net (64→32→4 with ReLU/Softmax)
       trains for *epochs* iterations, printing val‑set metrics each epoch.
    5. **Persistence** – `save()` writes three artefacts sharing the *save* stem:

       * `moodnet.keras` – Keras model weights & architecture.
       * `moodnet.meta` – pickled scaler + label encoder (via *joblib*).

    **Arguments**
    ▸ *CSV* – path to the dataset file from `build-dataset`.

    **Options**
    ▸ `--epochs` – training epochs (default 25).  
    ▸ `--save`   – output path prefix (default `model/moodnet.keras`).

    Example
    -------
    ```bash
    moodify train data/train.csv --epochs 30 --save weights/moodnet.keras
    ```
    This fits the network for 30 epochs and stores `weights/moodnet.keras` plus
    `weights/moodnet.meta`, which you can later load with `moodify curate`.
    """
    df = pd.read_csv(csv)
    net = MoodNet().fit(df, epochs=epochs)
    net.save(save)
    print(f"Training accuracy : {net.train_accuracy:.3f}")
    print(f"Validation accuracy: {net.val_accuracy:.3f}")
    typer.echo(f"✅  Model weights saved → {save}")

@app.command(help="Filter a live playlist *or* a pre-built CSV by predicted mood.")
def curate(
    mood: str = typer.Argument(..., help="Target mood to keep (Happy, Sad, etc.)"),
    # mutually-exclusive source options
    playlist: str = typer.Option(None, "--playlist", help="Source playlist URI to filter"),
    csv: pathlib.Path = typer.Option(None, "--csv", exists=True, help="Pre-built CSV to filter"),
    name: str = typer.Option("", help="Custom name for the new playlist"),
    public: bool = typer.Option(True, help="Make playlist public (default true)"),
    model_path: pathlib.Path = typer.Option("model/moodnet.keras", help="Trained model path"),
):
    """
    Create a mood-filtered playlist.

    Examples
    --------
    # live playlist
    moodify curate Happy --playlist spotify:playlist:37i9…

    # offline CSV
    moodify curate Sad --csv data/my_mix.csv --name "Offline Sad Mix"
    """
    sess = get_session()
    net = MoodNet.load(model_path)

    curator = Curator(sess, net)
    pl_id, n = curator.curate_playlist(
        target_mood=mood.title(),
        source_playlist=playlist,
        prebuilt_csv=csv,
        new_name=name or None,
        public=public,
    )
    typer.echo(f"✅  Created playlist ({n} tracks) → https://open.spotify.com/playlist/{pl_id}")

if __name__ == "__main__":
    app()