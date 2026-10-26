"""Persist selected recommendations separately from the searchable corpus."""

import json
import os
import tempfile
from pathlib import Path


def read_watchlist(path):
    path = Path(path)
    if not path.exists():
        return []
    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(entries, list) or any(
            not isinstance(entry, dict) or not all(
                isinstance(entry.get(key), str)
                for key in ("movie_id", "title", "release_date", "query", "plot")
            ) for entry in entries
        ):
            raise ValueError("Unexpected watchlist format")
        return entries
    except (json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"Cannot read watchlist at {path}; the file was left unchanged.") from error


def save_to_watchlist(path, match, query):
    """Save a movie once by ID, along with the search that led to it."""
    path = Path(path)
    entries = read_watchlist(path)
    metadata = match["metadata"]
    if any(entry["movie_id"] == metadata["movie_id"] for entry in entries):
        return False
    entries.append({
        "movie_id": metadata["movie_id"], "title": metadata["title"],
        "release_date": metadata.get("release_date", ""),
        "query": query, "plot": match["plot"],
    })
    path.parent.mkdir(parents=True, exist_ok=True)
    # Replace only after writing the complete JSON, protecting previous saves
    # from interruption during a write.
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         delete=False) as stream:
            temporary_path = Path(stream.name)
            json.dump(entries, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    return True
