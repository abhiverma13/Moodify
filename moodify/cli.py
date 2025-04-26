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
                # df = builder.add_genre(df)  # Optional: full list of Spotify genres for the track’s primary artist
                df["mood"] = m.title()
                frames.append(df)

    if not frames:
        typer.echo("⚠️  No matching playlists found.", err=True)
        raise typer.Exit(code=1)

    pd.concat(frames).to_csv(out, index=False)
    typer.echo(f"Saved {sum(len(f) for f in frames)} rows → {out}")

@app.command(help="Train the MoodNet neural network on a CSV and save the weights.")
def train(
    csv: pathlib.Path,
    epochs: int = 25,
    save: pathlib.Path = typer.Option("moodnet.h5", help="HDF5 file for model weights"),
):
    """Fit MoodNet using the supplied CSV and persist model + scaler + encoder."""
    df = pd.read_csv(csv)
    net = MoodNet().fit(df, epochs=epochs)
    net.save(save)
    typer.echo(f"✅  Model weights saved → {save}")

@app.command(
    help="Create a new playlist that contains only tracks whose predicted mood matches *mood*."
)
def curate(
    source_uri: str,
    mood: str,
    name: str = "",
    public: bool = True,
    model_path: pathlib.Path = "moodnet.h5",
):
    """Filter *source_uri* by predicted mood and write a new playlist to your library."""
    sess = get_session()
    net = MoodNet.load(model_path)

    curator = Curator(sess, net)
    pl_id, n = curator.curate_playlist(
        source_uri, mood.title(), new_name=name or None, public=public
    )
    typer.echo(
        f"✅  Created playlist ({n} tracks) → https://open.spotify.com/playlist/{pl_id}"
    )

if __name__ == "__main__":
    app()