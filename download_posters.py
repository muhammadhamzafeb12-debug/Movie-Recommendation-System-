#!/usr/bin/env python3
"""Download poster images for CineMatch locally. No personal API key required."""
import concurrent.futures
import json
import os
import re
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
POSTER_DIR = ROOT / "posters"
POSTER_DIR.mkdir(exist_ok=True)
DATASET = "ROSCOSMOS/Movie-Poster-WebURL-Dataset-1874-2025"
FILTER_URL = "https://datasets-server.huggingface.co/filter"
INDEX_FILE = POSTER_DIR / "poster_index.json"
TIMEOUT = 25


def norm(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def fetch_batch(ids):
    where = " OR ".join(f'"tmdb_id"={int(mid)}' for mid in ids)
    params = {
        "dataset": DATASET, "config": "default", "split": "train",
        "where": where, "offset": 0, "length": 100,
    }
    for attempt in range(4):
        try:
            response = requests.get(FILTER_URL, params=params, timeout=45)
            response.raise_for_status()
            rows = response.json().get("rows", [])
            found = {}
            for entry in rows:
                row = entry.get("row", {})
                mid, url = row.get("tmdb_id"), row.get("web_url")
                if mid is not None and isinstance(url, str) and url.startswith("https://image.tmdb.org/"):
                    found[str(int(mid))] = url.replace("/original/", "/w500/")
            return found
        except requests.RequestException as exc:
            if attempt == 3:
                print(f"  Batch failed: {exc}")
                return {}
            time.sleep(2 ** attempt)
    return {}


def download_one(item):
    mid, url = item
    target = POSTER_DIR / f"{mid}.jpg"
    if target.exists() and target.stat().st_size > 3000:
        return mid, str(target.relative_to(ROOT)), "cached"
    try:
        r = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": "CineMatch poster downloader"})
        r.raise_for_status()
        ctype = r.headers.get("Content-Type", "").lower()
        if "image" not in ctype or len(r.content) < 3000:
            return mid, None, "not-an-image"
        target.write_bytes(r.content)
        return mid, str(target.relative_to(ROOT)), "downloaded"
    except requests.RequestException:
        return mid, None, "failed"


def main():
    movies = pd.read_csv(ROOT / "tmdb_5000_movies.csv").drop_duplicates("id")
    ids = [int(x) for x in movies["id"].dropna().tolist()]
    print(f"CineMatch contains {len(ids)} unique TMDB movie IDs.")
    print("Step 1/3: finding public poster URLs (no API key)...")

    url_map = {}
    batch_size = 40
    batches = [ids[i:i + batch_size] for i in range(0, len(ids), batch_size)]
    for number, batch in enumerate(batches, 1):
        url_map.update(fetch_batch(batch))
        if number % 10 == 0 or number == len(batches):
            print(f"  Checked {min(number * batch_size, len(ids))}/{len(ids)} movie IDs; poster URLs: {len(url_map)}")

    # Fallback: the project's bundled 9K poster CSV, matched by normalized title.
    try:
        extra = pd.read_csv(ROOT / "9000plus.csv").dropna(subset=["Title", "Poster_Url"])
        extra_map = {norm(row.Title): row.Poster_Url for row in extra.itertuples()}
        for row in movies[["id", "title"]].itertuples(index=False):
            mid = str(int(row.id))
            if mid not in url_map:
                url = extra_map.get(norm(row.title))
                if isinstance(url, str) and url.startswith("https://"):
                    url_map[mid] = url.replace("/original/", "/w500/")
    except Exception as exc:
        print("  Optional 9K CSV fallback skipped:", exc)

    print(f"Step 2/3: downloading {len(url_map)} available posters locally...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(download_one, url_map.items()))

    index = {mid: path for mid, path, status in results if path}
    INDEX_FILE.write_text(json.dumps(index, indent=2), encoding="utf-8")
    downloaded = sum(1 for _, _, status in results if status == "downloaded")
    cached = sum(1 for _, _, status in results if status == "cached")
    failed = sum(1 for _, _, status in results if status in ("failed", "not-an-image"))
    missing = len(ids) - len(index)

    print("Step 3/3: complete.")
    print(f"Local posters ready: {len(index)} / {len(ids)}")
    print(f"New downloads: {downloaded}; already cached: {cached}; failed: {failed}")
    print(f"No usable poster found: {missing}")
    print("Poster cache saved in posters/ and can be reused offline.")
    print("Run: streamlit run app.py")


if __name__ == "__main__":
    main()
