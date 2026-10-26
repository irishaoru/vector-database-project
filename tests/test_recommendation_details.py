"""Test summary/trailer service contracts and failure paths without real credentials."""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
from urllib.error import URLError

from recommendation_details import RecommendationDetails
from search_movies import display_matches

MATCH = {"metadata": {"movie_id": "test", "title": "Ocean Garden", "release_date": "2003"},
         "plot": "A botanist cultivates luminous orchids under an alien ocean. Her failing submarine threatens the expedition."}
SUMMARY = MATCH["plot"].split(". ")[0] + "."


class RecommendationDetailsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.environment = patch.dict(os.environ, {"OLLAMA_MODEL": "test-model", "YOUTUBE_API_KEY": "test-secret", "MOVIE_DETAILS_MODE": ""})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.details = RecommendationDetails(cache_dir=self.temp.name)

    def test_summary_uses_full_plot_and_caches_success(self):
        with patch("recommendation_details.request_json", return_value={
            "done": True, "response": json.dumps({"sentence_ids": [0]})
        }) as request:
            self.assertEqual(self.details.summary(MATCH), (SUMMARY, "AI-selected summary"))
            payload = request.call_args.args[1]
            self.assertEqual(" ".join(json.loads(payload["prompt"])["sentences"].values()), MATCH["plot"])
            self.assertFalse(payload["stream"])
            self.assertEqual(self.details.summary(MATCH), (SUMMARY, "AI-selected summary"))
            self.assertEqual(request.call_count, 1)

    def test_changed_plot_does_not_reuse_summary(self):
        with patch("recommendation_details.request_json", return_value={
            "done": True, "response": json.dumps({"sentence_ids": [0]})
        }) as request:
            self.details.summary(MATCH)
            self.details.summary(MATCH | {"plot": MATCH["plot"] + " Another event occurs."})
            self.assertEqual(request.call_count, 2)

    def test_missing_or_bad_llm_falls_back_without_mislabeling(self):
        for response in [{"response": "invalid json"}, {"done": True, "response": '{"sentence_ids": [99]}'},
                         {"done": True, "response": '{"sentence_ids": [true]}'},
                         {"done": True, "done_reason": "length", "response": json.dumps({"sentence_ids": [0]})}]:
            self.details.ollama_unavailable = False
            with patch("recommendation_details.request_json", return_value=response):
                text, label = self.details.summary(MATCH)
                self.assertIn("excerpt", label)
                self.assertEqual(text, MATCH["plot"])
        self.details.ollama_unavailable = False
        with patch("recommendation_details.request_json", side_effect=URLError("offline")) as request:
            self.details.summary(MATCH)
            self.details.summary(MATCH)
            self.assertEqual(request.call_count, 1)

    def test_youtube_selects_matching_candidate_and_caches(self):
        response = {"items": [
            {"id": {"videoId": "wrong123456"}, "snippet": {"title": "Unrelated trailer"}},
            {"id": {"videoId": "abc123DEF45"}, "snippet": {
                "title": "Ocean Garden (2003) Official Trailer", "channelTitle": "Studio &amp; Co"}},
        ]}
        with patch("recommendation_details.request_json", return_value=response) as request:
            trailer = self.details.trailer(MATCH["metadata"])
            self.assertEqual(trailer["url"], "https://www.youtube.com/watch?v=abc123DEF45")
            self.assertEqual(trailer["channel"], "Studio & Co")
            self.assertIn("candidate", trailer["label"])
            self.assertEqual(self.details.trailer(MATCH["metadata"]), trailer)
            self.assertEqual(request.call_count, 1)

    def test_youtube_absent_key_quota_failure_and_no_results(self):
        self.details.youtube_key = ""
        with patch("recommendation_details.request_json") as request:
            self.assertIn("/results?", self.details.trailer(MATCH["metadata"])["url"])
            request.assert_not_called()
        self.details.youtube_key = "test-secret"
        for response in [{"items": []}, {"items": [{"id": {"videoId": "bad"}, "snippet": {"title": "Ocean Garden trailer"}}]}]:
            with patch("recommendation_details.request_json", return_value=response):
                self.assertIn("/results?", self.details.trailer(MATCH["metadata"])["url"])
        with patch("recommendation_details.request_json", side_effect=URLError("test-secret")):
            trailer = self.details.trailer(MATCH["metadata"])
            self.assertNotIn("test-secret", str(trailer))

    def test_display_preserves_search_plot_and_attaches_details(self):
        match = MATCH.copy()
        match["distance"] = 0.2
        output = io.StringIO()
        with patch("search_movies.RecommendationDetails", return_value=self.details), patch(
            "recommendation_details.request_json", side_effect=URLError("test-secret")
        ), redirect_stdout(output):
            display_matches("ocean expedition", [match])
        self.assertEqual(match["plot"], MATCH["plot"])
        self.assertIn("summary", match)
        self.assertIn("trailer", match)
        self.assertNotIn("test-secret", output.getvalue())


if __name__ == "__main__":
    unittest.main()
