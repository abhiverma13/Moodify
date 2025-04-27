#!/usr/bin/env python3
"""
fix_for_curate.py – sanitize any CSV so Moodify's --csv path works
---------------------------------------------------------------

Usage
-----
    python fix_for_curate.py --infile test.csv --outfile test_clean.csv
"""

import argparse
import pathlib
import sys
import pandas as pd

# ── Canonical feature list used inside Curator / MoodNet ────────────────
FEATURES = [
    "acousticness",
    "danceability",
    "energy",
    "instrumentalness",
    "liveness",
    "loudness",
    "speechiness",
    "tempo",
    "valence",
]
META_COLS = ["name", "uri"]            # track title & Spotify ID (string)
OPTIONAL = ["duration"]                # timedelta; ignored if absent
ALL_COLS = META_COLS + FEATURES + OPTIONAL


def load(path: pathlib.Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        sys.exit(f"❌  File not found: {path}")


def clean(df: pd.DataFrame) -> pd.DataFrame:
    # 1) Keep only expected columns, make an explicit copy
    df = df[[c for c in df.columns if c in ALL_COLS]].copy()

    # 2) Ensure all required columns exist
    missing = [c for c in META_COLS + FEATURES if c not in df.columns]
    if missing:
        sys.exit(f"❌  Missing columns: {', '.join(missing)}")

    # 3) Numeric features → float
    df.loc[:, FEATURES] = df[FEATURES].apply(pd.to_numeric, errors="coerce")

    # 4) Strip whitespace from string columns
    df.loc[:, META_COLS] = df[META_COLS].astype(str).apply(lambda s: s.str.strip())

    # 5) Parse duration
    if "duration" in df.columns:
        df["duration"] = pd.to_timedelta(df["duration"], errors="coerce")

    # 6) Re-order
    ordered = META_COLS + FEATURES + (["duration"] if "duration" in df.columns else [])
    return df[ordered]

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", required=True, type=pathlib.Path)
    ap.add_argument("--outfile", default="test_clean.csv", type=pathlib.Path)
    args = ap.parse_args(argv)

    df_raw = load(args.infile)
    df_clean = clean(df_raw)
    df_clean.to_csv(args.outfile, index=False)
    print(f"✅  Saved cleaned CSV → {args.outfile}  ({len(df_clean)} rows)")


if __name__ == "__main__":
    main()
