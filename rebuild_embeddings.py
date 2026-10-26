"""Copy every existing movie to a separate Nomic collection, preserving IDs."""

import argparse

import chromadb

from nomic_embeddings import NomicEmbeddingFunction
import legacy_jina_embeddings  # Registers the original model for reading old collections.
from load_movies import STORE

TARGET_COLLECTION = "movie_full_plots_nomic_v15"


def rebuild(client, source_name, target_name=TARGET_COLLECTION):
    if source_name == target_name:
        raise ValueError("Source and target collections must be different")
    source = client.get_collection(source_name, embedding_function=None)
    records = source.get(include=["documents", "metadatas"])
    embedding = NomicEmbeddingFunction()
    # Validate the complete corpus before beginning migration.
    counts = [embedding.token_count(plot) for plot in records["documents"]]
    if any(count > 8192 for count in counts):
        raise ValueError("A plot exceeds Nomic's input limit. Nothing was truncated.")
    target = client.get_or_create_collection(target_name, embedding_function=embedding,
        configuration={"hnsw": {"space": "cosine"}})
    for start in range(0, len(records["ids"]), 10):
        end = start + 10
        target.upsert(ids=records["ids"][start:end], documents=records["documents"][start:end],
            metadatas=[m | {"token_count": count} for m, count in
                       zip(records["metadatas"][start:end], counts[start:end])])
        print(f"Re-embedded {min(end, len(counts))}/{len(counts)} movies", flush=True)
    copied = target.get(ids=records["ids"], include=["documents"])
    assert dict(zip(copied["ids"], copied["documents"])) == dict(zip(records["ids"], records["documents"]))
    print("Verified every movie ID and full plot was preserved. Original collection and watchlist unchanged.")
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="movie_full_plots_jina_v2")
    args = parser.parse_args()
    rebuild(chromadb.PersistentClient(path=str(STORE)), args.source)


if __name__ == "__main__":
    main()
