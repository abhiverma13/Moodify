import typer, pandas as pd, pathlib
from moodify.auth import CredentialStore
from moodify.client import MoodifySession
from moodify.data import DataBuilder
from moodify.model import MoodNet
from moodify.recommender import Curator

app = typer.Typer(help="🎧 Moodify – mood-based playlists")

# ── Global objects shared by commands ───────────────────────────────────
store = CredentialStore(); sess = MoodifySession(store)

@app.command()
def playlists(owned_only: bool = typer.Option(False, "--mine", help="Only show playlists you own")):
    for p in sess.playlists(owned_only=owned_only):
        typer.echo(f"{p['name']} → {p['uri']}")

@app.command()
def build_dataset(*moods: str, out: pathlib.Path = typer.Option("dataset.csv")):
    """Export a CSV with track‑level features and an inferred *mood* label.
    Tracks are pulled from any playlist whose *title* contains the mood string."""
    builder = DataBuilder(sess)
    frames = []
    for m in moods:
        for p in sess.playlists():
            if m.lower() in p["name"].lower():
                df = builder.with_audio_features(builder.playlist_df(p["uri"]))
                df["mood"] = m.title()
                frames.append(df)
    pd.concat(frames).to_csv(out, index=False)
    typer.echo(f"Saved {sum(len(f) for f in frames)} rows → {out}")

@app.command()
def train(csv: pathlib.Path, epochs: int = 25, save: pathlib.Path = typer.Option("moodnet.h5")):
    df = pd.read_csv(csv)
    net = MoodNet().fit(df, epochs=epochs)
    net.save(save)
    typer.echo(f"Model weights saved → {save}")

@app.command()
def curate(source_uri: str, mood: str, name: str = "", public: bool = True, model_path: pathlib.Path = "moodnet.h5"):
    net = MoodNet.load(model_path)
    curator = Curator(sess, net)
    pl_id, n = curator.curate_playlist(source_uri, mood.title(), new_name=name or None, public=public)
    typer.echo(f"✅  Created playlist ({n} tracks) → https://open.spotify.com/playlist/{pl_id}")

if __name__ == "__main__":
    app()