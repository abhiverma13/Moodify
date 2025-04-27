#!/usr/bin/env python3
"""
fix_dataset.py  –  bring an arbitrary train.csv into the canonical Moodify format
--------------------------------------------------------------------------
Run inside the virtual-env:

    python fix_dataset.py --infile train.csv --outfile train_clean.csv
"""

import argparse
import pathlib
import sys
import pandas as pd

# Expected schema (order does not matter when saving)
NUMERIC_COLS = [
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
STR_COLS = ["name", "uri", "artist", "mood"]
DURATION_COL = "duration"          # pandas.Timedelta
EXPECTED_COLS = STR_COLS + NUMERIC_COLS + [DURATION_COL]


def load_csv(path: pathlib.Path) -> pd.DataFrame:
    """Read CSV, letting pandas infer dtypes first."""
    try:
        return pd.read_csv(path)
    except FileNotFoundError as e:
        sys.exit(f"❌  File not found: {e.filename}")


def harmonise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename/convert columns so they match the build_dataset output."""
    # 1) Drop genre columns if present
    df = df.drop(columns=[c for c in df.columns if c.lower().startswith("genre")], errors="ignore")

    # 2) Rename 'length' or 'duration_ms' to 'duration'
    if "length" in df.columns:
        df = df.rename(columns={"length": "duration"})
    if "duration_ms" in df.columns:
        df["duration"] = pd.to_timedelta(df["duration_ms"], unit="ms")
        df = df.drop(columns="duration_ms")

    # 3) Ensure duration is pandas.Timedelta
    if "duration" in df.columns and not pd.api.types.is_timedelta64_dtype(df["duration"]):
        # try to parse string like '0 days 00:03:45'
        df["duration"] = pd.to_timedelta(df["duration"], errors="coerce")

    # 4) Cast numeric cols to float
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 5) Ensure string columns are dtype 'object' and strip whitespace
    for col in STR_COLS:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # 6) Re-order / subset
    missing = [c for c in EXPECTED_COLS if c not in df.columns]
    if missing:
        sys.exit(f"❌  Missing required columns: {missing}")

    df = df[EXPECTED_COLS]          # drop extras, keep expected order
    return df


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Normalize Moodify training CSV")
    parser.add_argument("--infile", required=True, type=pathlib.Path, help="Path to the raw train.csv")
    parser.add_argument(
        "--outfile",
        default="train_clean.csv",
        type=pathlib.Path,
        help="Where to write the cleaned CSV (default: train_clean.csv)",
    )
    args = parser.parse_args(argv)

    df_raw = load_csv(args.infile)
    df_clean = harmonise_columns(df_raw)

    df_clean.to_csv(args.outfile, index=False)
    print(f"✅  Clean CSV saved → {args.outfile}  ({len(df_clean)} rows)")


if __name__ == "__main__":
    main()