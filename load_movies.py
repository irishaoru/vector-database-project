"""Load a small CMU movie sample into a persistent local Chroma collection."""

import argparse
import csv
import io
import json
import tarfile
from pathlib import Path

import chromadb
from movie_embeddings import MAX_TOKENS, MovieEmbeddingFunction


ROOT = Path(__file__).resolve().parent
STORE = ROOT / "chroma_store"
COLLECTION = "movie_full_plots_jina_v2"


def read_movies(archive_path, limit):
    """Join metadata and plots by Wikipedia movie ID without extracting files."""
    with tarfile.open(archive_path, "r:gz") as archive:
        metadata_file = archive.extractfile("MovieSummaries/movie.metadata.tsv")
        with io.TextIOWrapper(metadata_file, encoding="utf-8") as stream:
            metadata = {row[0]: row for row in csv.reader(stream, delimiter="\t")}

        plot_file = archive.extractfile("MovieSummaries/plot_summaries.txt")
        with io.TextIOWrapper(plot_file, encoding="utf-8") as stream:
            movies = []
            for line in stream:
                movie_id, separator, plot = line.rstrip("\n").partition("\t")
                row = metadata.get(movie_id)
                if not separator or not plot.strip() or not row or len(row) < 9:
                    continue
                movies.append({
                    "movie_id": movie_id,
                    "title": row[2],
                    "release_date": row[3],
                    "genres": row[8],
                    "plot": plot,
                })
                if len(movies) == limit:
                    return movies
    return movies


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True,
                        help="Path to the downloaded MovieSummaries.tar.gz")
    parser.add_argument("--limit", type=int, default=50,
                        help="Number of movies to load (default: 50)")
    args = parser.parse_args()
    if not args.archive.is_file():
        parser.error(f"Archive not found: {args.archive}")
    if args.limit < 1:
        parser.error("--limit must be a positive integer")

    movies = read_movies(args.archive, args.limit)
    if not movies:
        parser.error("No movies with plots and metadata found")
    print(f"Read {len(movies)} movies. Preparing Jina full-plot embeddings...", flush=True)
    embedding = MovieEmbeddingFunction()

    documents, ids, metadatas = [], [], []
    for movie in movies:
        token_count = embedding.token_count(movie["plot"])
        if token_count > MAX_TOKENS:
            parser.error(f"{movie['title']} has {token_count} tokens; the model limit "
                         f"is {MAX_TOKENS}. Nothing was truncated or loaded.")
        documents.append(movie["plot"])
        ids.append(f"cmu:{movie['movie_id']}")
        year = movie["release_date"][:4]
        genres = list(json.loads(movie["genres"]).values())
        metadatas.append({
            key: movie[key]
            for key in ("movie_id", "title", "release_date", "genres")
        } | {"token_count": token_count, "source": "CMU Movie Summary Corpus",
             "release_year": int(year) if year.isdigit() else 0,
             "is_romantic_comedy": "Romantic comedy" in genres})

    client = chromadb.PersistentClient(path=str(STORE))
    collection = client.get_or_create_collection(
        name=COLLECTION, embedding_function=embedding,
        configuration={"hnsw": {"space": "cosine"}},
    )
    for start in range(0, len(ids), 50):
        end = start + 50
        # Stable IDs and upsert make reloading this same corpus safe.
        collection.upsert(ids=ids[start:end], documents=documents[start:end],
                          metadatas=metadatas[start:end])
        print(f"Stored {min(end, len(ids))}/{len(ids)} full movie plots", flush=True)
    print(f"Loaded {len(movies)} movies, one full plot per item.")
    print(f"Collection now contains {collection.count()} movies.")
    print(f"Database folder: {STORE}")


if __name__ == "__main__":
    main()
