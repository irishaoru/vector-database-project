"""Check that the pilot summaries stay grounded and failures are explicit."""

import json
import tempfile
import unittest
from unittest.mock import patch

from compare_plot_summaries import make_synopsis
from recommendation_details import RecommendationDetails


class SummaryExperimentTest(unittest.TestCase):
    def test_short_plot_unchanged_without_llm(self):
        with tempfile.TemporaryDirectory() as directory:
            details = RecommendationDetails(directory)
            with patch("compare_plot_summaries.request_json") as request:
                self.assertEqual(make_synopsis(details, "Title", "A short source plot."),
                                 ("A short source plot.", "already_short"))
                request.assert_not_called()

    def test_selected_sentences_are_original_order_and_cached(self):
        sentences = [" ".join([word] * 30) + "." for word in ["Beginning", "Middle", "Ending"]]
        plot = " ".join(sentences)
        with tempfile.TemporaryDirectory() as directory:
            details = RecommendationDetails(directory)
            with patch("compare_plot_summaries.request_json", return_value={
                "done": True, "response": json.dumps({"sentence_ids": [2, 0]})
            }) as request:
                summary, method = make_synopsis(details, "Title", plot)
                self.assertEqual(summary, sentences[0] + " " + sentences[2])
                self.assertEqual(method, "llm_selected")
                self.assertEqual(make_synopsis(details, "Title", plot)[0], summary)
                self.assertEqual(request.call_count, 1)
                payload = request.call_args.args[1]
                self.assertEqual(" ".join(json.loads(payload["prompt"])["sentences"].values()), plot)

    def test_invalid_selection_is_not_silently_replaced(self):
        plot = " ".join(["Word"] * 80) + "."
        with tempfile.TemporaryDirectory() as directory:
            details = RecommendationDetails(directory)
            with patch("compare_plot_summaries.request_json", return_value={
                "done": True, "response": '{"sentence_ids": [99]}'
            }):
                with self.assertRaises(ValueError):
                    make_synopsis(details, "Title", plot)


if __name__ == "__main__":
    unittest.main()
