"""Interactive movie search: add plots and search without restarting."""

import json
from uuid import uuid4

import chromadb

from load_movies import COLLECTION, STORE
from movie_embeddings import MAX_TOKENS, MovieEmbeddingFunction
from search_movies import build_filters, display_matches, search_movies
from watchlist import read_watchlist, save_to_watchlist


def add_movie(collection, embedding, title, plot, year="", genres=""):
    title, plot, year = title.strip(), plot.strip(), str(year).strip()
    if not title or not plot:
        raise ValueError("A title and plot description are required.")
    if year and (not year.isdigit() or not 1000 <= int(year) <= 9999):
        raise ValueError("Enter a four-digit release year, or leave it blank.")
    count = embedding.token_count(plot)
    if count > MAX_TOKENS:
        raise ValueError(f"The plot has {count} tokens; the limit is {MAX_TOKENS}.")
    genre_list = [g.strip() for g in genres.split(",") if g.strip()]
    movie_id = "user:" + uuid4().hex
    collection.add(ids=[movie_id], documents=[plot], metadatas=[{
        "movie_id": movie_id, "title": title, "release_date": year,
        "release_year": int(year) if year else 0,
        "genres": json.dumps(genre_list),
        "is_romantic_comedy": any(g.lower() in {"romantic comedy", "romcom", "rom com"}
                                 for g in genre_list),
        "token_count": count, "source": "User-entered movie",
    }])
    return movie_id


def main():
    print("Preparing movie search...", flush=True)
    embedding = MovieEmbeddingFunction()
    collection = chromadb.PersistentClient(path=str(STORE)).get_or_create_collection(
        COLLECTION, embedding_function=embedding,
        configuration={"hnsw": {"space": "cosine"}},
    )
    try:
        while True:
            print(f"\n--- Movie Finder ({collection.count()} movies) ---")
            print("1. Search\n2. Add a movie\n3. Quit\n4. View saved watchlist")
            choice = input("Choose an option: ").strip()
            try:
                if choice == "1":
                    query = input("What do you want to watch? ").strip()
                    if not query:
                        raise ValueError("Enter a description to search for.")
                    where, labels = build_filters(query)
                    matches = search_movies(collection, query, where=where)
                    display_matches(query, matches, labels)
                    while matches:
                        selection = input(f"\nSave result 1–{len(matches)} to watchlist (Enter to finish): ").strip()
                        if not selection:
                            break
                        if not selection.isdigit() or not 1 <= int(selection) <= len(matches):
                            print("Enter one of the displayed result numbers.")
                            continue
                        match = matches[int(selection) - 1]
                        added = save_to_watchlist(STORE / "watchlist.json", match, query)
                        title = match["metadata"]["title"]
                        print(f"Saved {title} to your watchlist." if added else f"{title} is already on your watchlist.")
                elif choice == "2":
                    title = input("Movie title: ")
                    year = input("Release year (optional): ")
                    genres = input("Genres, separated by commas (optional): ")
                    print("Enter the plot; finish with an empty line:")
                    lines = []
                    while (line := input()).strip():
                        lines.append(line)
                    add_movie(collection, embedding, title, "\n".join(lines), year, genres)
                    print(f"Saved {title.strip()}. You can search for it now.")
                elif choice == "3":
                    print("Goodbye!")
                    return
                elif choice == "4":
                    entries = read_watchlist(STORE / "watchlist.json")
                    if not entries:
                        print("Your watchlist is empty. Search and select a result to save.")
                    else:
                        print("\n--- Saved watchlist ---")
                        for number, entry in enumerate(entries, 1):
                            year = entry["release_date"][:4] or "date unknown"
                            print(f"{number}. {entry['title']} ({year})")
                            print(f"   Found while searching: {entry['query']}")
                else:
                    print("Choose 1, 2, 3, or 4.")
            except (ValueError, OSError) as error:
                print(f"Could not complete that action: {error}")
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye! Saved movies remain in the database.")


if __name__ == "__main__":
    main()
