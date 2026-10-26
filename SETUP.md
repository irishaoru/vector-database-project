# Local setup and sample loading

Use Python 3.10 or newer. From the repository folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python load_movies.py --archive /path/to/MovieSummaries.tar.gz --limit 50
```

On this machine, the archive is `/Users/irishao/Downloads/MovieSummaries.tar.gz`.
The loader reads the archive directly, joins titles and plots by Wikipedia movie
ID, and embeds each full plot as one item. Titles, release dates, genres, movie
IDs, and token counts are saved as metadata.

The local [Jina v2 small English embedding model](https://huggingface.co/jinaai/jina-embeddings-v2-small-en)
downloads on first use (about 130 MB). It requires no API key. We use the official
ONNX export with mean pooling, normalized vectors, and cosine distance.
The model stays in `.cache/` and the persistent database stays in
`chroma_store/`, both relative to this project. Both are ignored by Git.
The archive and any files in `data/` are also ignored.

Loading the same sample again updates the same movie IDs instead of adding
duplicates. Increasing `--limit` adds more movies; decreasing it does not remove
movies already loaded. Start with 50, then try a few hundred once search works.
The working local collection has now been expanded to 500 movies. To reproduce it:

```sh
python load_movies.py --archive /path/to/MovieSummaries.tar.gz --limit 500
```

The corpus comes from 2012-era sources, so it cannot recommend recent releases
that are absent from that dataset.

## Search the sample

For the interactive app, run:

```sh
python app.py
```

Choose **2. Add a movie**, enter a title, optional release year, optional genres
(comma-separated, e.g. `Romantic comedy, Drama`), and a plot description.
Finish the plot with an empty line. Then choose **1. Search** in the same running
program. The new plot is embedded immediately and saved to the same persistent
collection as the downloaded movies. Quit and reopen to keep searching it.
Empty titles/plots, invalid years, and over-limit plots are rejected. A unique ID
is generated for each addition. This does not detect duplicate movie titles.

### Save recommendations to a watchlist

After a search in `app.py`, enter a result number to save that movie. You can
save additional results, then press Enter to return to the menu. Choose
**4. View saved watchlist** to see your selected movies and the searches that led
to them. Saving the same movie ID again does not create a duplicate.

Choose **5. Remove a watchlist movie**, then enter its displayed number to remove
one entry. Press Enter to cancel. Removal is saved immediately and survives
restarting; it does not delete the movie from the searchable Chroma collection.
You can search for and save that movie again to get its current summary and link.

The watchlist is saved locally in `chroma_store/watchlist.json`, which is ignored
by Git. It survives quitting and restarting. Choose **3. Quit**, run `python app.py`
again, and choose **4** to check. Movie additions remain in Chroma as well.
The one-shot `search_movies.py` command only searches; use `app.py` for saving.

### Short summaries and trailer links

Search still embeds and retrieves **full plots** with Jina/Chroma. After retrieval,
only the top three plots are sent to a separate local language model to create short
extractive summaries. The model selects up to three original plot sentences; the app
validates their indices and assembles the selected text in source order. This avoids
invented plot details encountered during tests with freely rewritten summaries.
Summaries do not replace the stored plots or change ranking.

1. Install [Ollama](https://ollama.com/download) and start it. In a terminal, download
   the small [Qwen2.5 1.5B model](https://ollama.com/library/qwen2.5:1.5b):

   ```sh
   ollama pull qwen2.5:1.5b
   ```

   This model download is about 986 MB; runtime memory is larger. If the service
   isn't already running, use `ollama serve` in another terminal.
   On the current development machine, a portable runtime and the model have
   already been downloaded into the ignored project cache. You can start it with
   `python start_summary_server.py` in a separate terminal and leave that running.
   Those downloads are not included in Git; other users should install Ollama.
2. Copy `.env.example` to `.env`. The defaults use Ollama at
   `http://127.0.0.1:11434` with `qwen2.5:1.5b`. Change `OLLAMA_MODEL` to use another
   installed model if you prefer. A small model is lightweight but may make mistakes.
3. For direct trailer candidates, create a Google Cloud project, enable **YouTube
   Data API v3**, create an API key, and enter it as `YOUTUBE_API_KEY` in `.env`.
   Restrict the key to that API. Follow Google's
   [setup instructions](https://developers.google.com/youtube/v3/getting-started).
   Never commit `.env` or paste a real key into documentation/chat.
4. Run `python app.py` or `python search_movies.py` as before.

Each recommendation shows an AI-selected summary and a trailer link. The model is
instructed to avoid ending spoilers, but its selections can still omit context or
reveal spoilers, and the source itself may have errors. It does not invent trailer URLs:
the [YouTube search endpoint](https://developers.google.com/youtube/v3/docs/search/list)
finds video candidates using title, year, and “official trailer.” Matching video
titles and channels are displayed; the result is a candidate, not a guarantee of
the correct film or official ownership.

Without Ollama, the app clearly labels a short **plot excerpt** instead of an AI
summary. Without a YouTube key, or if the API fails or no candidate matches, it
shows a **YouTube search link** instead of claiming to have found a trailer.
Network calls have timeouts, and failures do not prevent searching or saving.
Ollama receives the full retrieved plot locally; YouTube receives only title/year
search terms and your API credential. Changing `OLLAMA_URL` changes where plots
are sent.

Successful summaries are cached by plot content/model/prompt version under
`.cache/recommendations/`; changing a plot triggers a new summary. Trailer
candidates expire after 24 hours to limit repeated API calls while refreshing
links. Google controls API quotas; check your project's console for limits.
Delete this cache to regenerate summaries. Saved watchlist entries retain the
displayed summary and trailer link; older entries still work without those fields.

For diagnostics, `python search_movies.py "your request" --full-plots` shows the
original plots without calling the summary/trailer services. Set
`MOVIE_DETAILS_MODE=offline` in `.env` to use labeled excerpts/search links.

With the virtual environment activated, run:

```sh
python search_movies.py "Youngsters forced into a lethal survival contest by an oppressive regime."
python search_movies.py "An innocent mother becomes the target of sensational journalism after a tragedy."
```

Or run `python search_movies.py` and enter your own description when prompted.
The script shows three movies, each with its full plot.
Movies are ranked by the similarity of their full plots. Distance is not a confidence percentage, and
the closest movies may still be irrelevant. Read the matching text to evaluate
the result. These examples must be rechecked after loading more movies.

### Release years and romantic-comedy filtering

```sh
python search_movies.py "a light hearted romantic comedy from the early 2000s"
python search_movies.py "a comforting story about starting over" --year-from 2000 --year-to 2005
```

The script recognizes decade phrases such as `early 2000s` (2000–2005),
`mid 2000s` (2003–2007), `late 2000s` (2006–2009), and `2000s` (2000–2009).
Explicit year flags override decade recognition. Both endpoints are inclusive.
Other date phrasing should use the year flags; this is not a general language parser.
Unknown release dates are excluded when a date filter is active.

Requests containing `romantic comedy`, `romcom`, or `rom com` require the dataset's
`Romantic comedy` genre tag. This may miss movies whose genre metadata is incomplete.
Applied filters are displayed. Mood and story preferences still use vector similarity
within that eligible set. If no titles qualify, the app says so instead of returning
movies outside the filters. Rerun the loader to populate these metadata fields in an
older collection.

## Full plots and the model limit

The model supports up to 8,192 tokens (words or pieces of words) per item.
Plots are no longer split into passages. The loader checks all selected plots
before writing; if one exceeds the limit, it reports the title and stops instead
of silently cutting off text. Search queries are checked too.

The new collection is `movie_full_plots_jina_v2`. The previous MiniLM passage
collection is retained separately, but search now uses only the Jina collection.
Different models' embeddings must not be mixed. Model files are pinned to a
specific revision in `movie_embeddings.py`; loading and searching share that code.

## Recheck the two semantic examples

```sh
python verify_semantic_examples.py
```

This runs both examples with no date or genre filters, reports the expected movie's
rank among the top three, and records literal word overlap with its full plot.
The actual output is saved in `semantic_search_results.json`. These were chosen
after testing several candidate searches; not all candidates succeeded. Rankings
may change as movies are added, so rerun before recording your demo. Use this
evidence to write the required README explanation in your own words. These examples
demonstrate retrieval on this corpus, not perfect recommendations for every query.

To verify the real add/search/restart menu flow using a temporary database:

```sh
python -m unittest discover -s tests -v
```

The loader, semantic search with optional metadata filters, interactive adding,
and a saved watchlist are implemented. Retrieval supplies movie choices that users
can select and organize into a persistent personal list, with the original search
recorded for context.

Data source: [CMU Movie Summary Corpus](https://www.cs.cmu.edu/~ark/personas/).
The included dataset README credits David Bamman, Brendan O'Connor, and Noah
Smith, “Learning Latent Personas of Film Characters,” ACL 2013, and states that
the corpus is released under a Creative Commons Attribution-ShareAlike license.

This setup guide was AI-generated. Write the required README sections yourself
and keep a separate prompt log as described in the assignment.
