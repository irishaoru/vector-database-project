"""Exercise the real terminal add/search/restart flow in an isolated database."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import chromadb

from app import add_movie
from load_movies import COLLECTION
from movie_embeddings import MovieEmbeddingFunction
from watchlist import read_watchlist, save_to_watchlist

ROOT = Path(__file__).resolve().parents[1]


class MovieAppTest(unittest.TestCase):
    def test_add_search_restart_and_validation(self):
        plot = "A botanist breeds luminous orchids aboard a submarine beneath Europa's frozen ocean."
        with tempfile.TemporaryDirectory() as directory:
            code = "from pathlib import Path; import app; app.STORE=Path(" + repr(directory) + "); app.main()"

            def run_menu(user_input):
                result = subprocess.run(
                    [sys.executable, "-c", code], input=user_input,
                    text=True, capture_output=True, cwd=ROOT, timeout=120,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                return result.stdout

            first = run_menu("4\n2\nOcean Garden\n2003\nRomantic comedy\n" + plot + "\n\n1\n" + plot + "\n9\n1\n1\n\n3\n")
            self.assertIn("Your watchlist is empty.", first)
            self.assertIn("Saved Ocean Garden. You can search for it now.", first)
            self.assertIn("1. Ocean Garden (2003)", first)
            self.assertIn("Saved Ocean Garden to your watchlist.", first)
            self.assertIn("Ocean Garden is already on your watchlist.", first)
            entries = read_watchlist(Path(directory) / "watchlist.json")
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["query"], plot)
            second = run_menu("4\n1\n" + plot + "\n\n3\n")
            self.assertIn("--- Saved watchlist ---", second)
            self.assertIn("Found while searching: " + plot, second)
            self.assertIn("1. Ocean Garden (2003)", second)
            client = chromadb.PersistentClient(path=directory)
            embedding = MovieEmbeddingFunction()
            collection = client.get_collection(COLLECTION, embedding_function=embedding)
            self.assertEqual(collection.count(), 1)
            for title, description, year in [("", plot, "2003"), ("Title", "", ""),
                                             ("Title", plot, "yesterday"),
                                             ("Title", "hello " * 8200, "2003")]:
                with self.assertRaises(ValueError):
                    add_movie(collection, embedding, title, description, year)
            self.assertEqual(collection.count(), 1)
            second_id = add_movie(collection, embedding, "Ocean Garden", plot, "2003")
            self.assertTrue(second_id.startswith("user:"))
            self.assertEqual(collection.count(), 2)  # Same title never reuses an ID.

    def test_corrupt_watchlist_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "watchlist.json"
            for content in ["unfinished JSON", '{}', '[{"movie_id": "broken"}]']:
                path.write_text(content)
                with self.assertRaises(ValueError):
                    save_to_watchlist(path, {}, "query")
                self.assertEqual(path.read_text(), content)


if __name__ == "__main__":
    unittest.main()
