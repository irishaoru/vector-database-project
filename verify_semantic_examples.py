"""Recheck two semantic examples against the current collection, without filters."""

import json
import re

import chromadb

from load_movies import COLLECTION, ROOT, STORE
from movie_embeddings import MODEL, REVISION, MovieEmbeddingFunction
from search_movies import search_movies

EXAMPLES = [
    {"query": "An anthology connecting unrelated lives through the same firearm.",
     "expected_movie_id": "34410222", "expected_title": "The Gun"},
    {"query": "A housebound woman fears she imagined a homicide because nobody can verify her account.",
     "expected_movie_id": "4072739", "expected_title": "Frozen with Fear"},
]


def words(text):
    return set(re.findall(r"\b\w+\b", text.lower()))


def main():
    collection = chromadb.PersistentClient(path=str(STORE)).get_collection(
        COLLECTION, embedding_function=MovieEmbeddingFunction(),
    )
    report = {"model": MODEL, "revision": REVISION, "collection": COLLECTION,
              "movie_count": collection.count(), "metadata_filters_used": False,
              "top_k": 3, "examples": []}
    passed = True
    for example in EXAMPLES:
        target = collection.get(where={"movie_id": example["expected_movie_id"]},
                                include=["documents"])
        if not target["documents"]:
            raise SystemExit(f"Missing {example['expected_title']}; load the 500-movie sample first.")
        plot = target["documents"][0]
        results = search_movies(collection, example["query"])
        rank = next((i for i, m in enumerate(results, 1)
                     if m["metadata"]["movie_id"] == example["expected_movie_id"]), None)
        overlap = sorted(words(example["query"]) & words(plot))
        # These are the only shared words allowed for these particular examples.
        no_keyword_overlap = set(overlap) <= {"a", "her", "the"}
        success = rank is not None and no_keyword_overlap
        passed = passed and success
        report["examples"].append(example | {
            "expected_plot": plot, "rank": rank, "shared_words": overlap,
            "passed": success,
            "results": [{"title": m["metadata"]["title"],
                         "movie_id": m["metadata"]["movie_id"],
                         "distance": m["distance"]} for m in results],
        })
        print(f"{example['expected_title']}: rank {rank or 'outside top 3'}; shared words: {overlap}")
    destination = ROOT / "semantic_search_results.json"
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"Saved actual results to {destination}")
    if not passed:
        raise SystemExit("An example failed. Review the report; rankings can change as data grows.")


if __name__ == "__main__":
    main()
