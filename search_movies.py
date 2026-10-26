"""Search stored movie plots by meaning and display distinct movie matches."""

import argparse
import re
import textwrap

import chromadb
from chromadb.errors import NotFoundError
from movie_embeddings import MovieEmbeddingFunction

from load_movies import COLLECTION, STORE


def build_filters(query, year_from=None, year_to=None):
    """Recognize a few explicit preferences; keep mood matching semantic."""
    filters = []
    labels = []
    # Interpret early as years 0–5, mid as 3–7, late as 6–9 of a decade.
    decade = re.search(r"\b(?:(early|mid|late)[ -]+)?((?:19|20)\d0)s\b", query, re.I)
    if decade and year_from is None and year_to is None:
        part, start = decade.groups()
        start = int(start)
        offsets = {"early": (0, 5), "mid": (3, 7), "late": (6, 9)}
        low, high = offsets.get((part or "").lower(), (0, 9))
        year_from, year_to = start + low, start + high
    if year_from is not None and year_to is not None and year_from > year_to:
        raise ValueError("The starting year must not exceed the ending year")
    if year_from is not None or year_to is not None:
        # Unknown release years are stored as 0 and must not pass a date filter.
        filters.append({"release_year": {"$gte": year_from if year_from is not None else 1}})
        if year_to is not None:
            filters.append({"release_year": {"$lte": year_to}})
        labels.append(f"release years {year_from or 'any'}–{year_to or 'any'}")
    if re.search(r"\b(?:romantic[ -]+comedy|rom[ -]?com)\b", query, re.I):
        filters.append({"is_romantic_comedy": True})
        labels.append("genre: Romantic comedy")
    where = {"$and": filters} if len(filters) > 1 else (filters[0] if filters else None)
    return where, labels


def search_movies(collection, query, limit=3, where=None):
    """Return movies ranked by similarity of their full plots."""
    count = len(collection.get(where=where, include=[])["ids"]) if where else collection.count()
    if not count:
        return []
    options = {"where": where} if where else {}
    results = collection.query(
        query_texts=[query], n_results=min(count, limit),
        include=["documents", "metadatas", "distances"],
        **options,
    )
    # Chroma returns one inner list per query. We submitted one query.
    return [
        {"metadata": metadata, "plot": document, "distance": distance}
        for document, metadata, distance in zip(
            results["documents"][0], results["metadatas"][0],
            results["distances"][0],
        )
    ]


def display_matches(query, matches, labels=()):
    """Show results consistently in the one-shot script and interactive app."""
    if not matches:
        print("No stored movies meet those filters. Try a wider year range or load more movies.")
        return
    print(f"\nClosest movies for: {query.strip()}")
    if labels:
        print("Filters: " + "; ".join(labels))
    print("These are similarity matches; review the plots to judge relevance.")
    for rank, match in enumerate(matches, 1):
        metadata = match["metadata"]
        year = metadata.get("release_date", "")[:4] or "date unknown"
        print(f"\n{rank}. {metadata['title']} ({year})")
        print(f"   Distance: {match['distance']:.4f} (lower means closer; not a probability)")
        print("   Full plot (may contain spoilers):")
        print(textwrap.fill(match["plot"], width=88,
                            initial_indent="   ", subsequent_indent="   "))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", help="Describe what you want to watch")
    parser.add_argument("--year-from", type=int, help="Earliest release year (inclusive)")
    parser.add_argument("--year-to", type=int, help="Latest release year (inclusive)")
    args = parser.parse_args()
    try:
        query = args.query if args.query is not None else input("What do you want to watch? ")
    except (EOFError, KeyboardInterrupt):
        print("\nSearch cancelled.")
        return
    if not query.strip():
        parser.error("Enter a description to search for")
    try:
        where, labels = build_filters(query, args.year_from, args.year_to)
    except ValueError as error:
        parser.error(str(error))
    if not (STORE / "chroma.sqlite3").is_file():
        parser.error("No database found. Run load_movies.py first (see SETUP.md).")

    embedding = MovieEmbeddingFunction()
    client = chromadb.PersistentClient(path=str(STORE))
    try:
        collection = client.get_collection(COLLECTION, embedding_function=embedding)
    except NotFoundError:
        parser.error("Movie collection not found. Run load_movies.py first.")
    try:
        matches = search_movies(collection, query.strip(), where=where)
    except ValueError as error:
        parser.error(str(error))
    display_matches(query, matches, labels)


if __name__ == "__main__":
    main()
