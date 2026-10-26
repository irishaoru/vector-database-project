# Prompt log — movie recommendation app

## Tool used:
OpenAI Codex GPT-6.1 Sol Light

### What the tool was used for:
The AI wrote much of the code and the automated tests. I guided the feature choices, tried searches, questioned weak recommendations and asked it to test different embedding models and try to use summaries instead of full descriptions, asked for explanations on the set up and how the vector database was implemented, and wrote my README draft. I also read the assignment before asking for clarification on some areas using AI and discussing the project direction with my professor.

### The process: 

## 1. Understanding the assignment and choosing an idea

Important prompts:

```not sure what the professor means by write two searches? like this?: "recommend me a movie that is dsytopian and modern, with a little bit of comedy in it as well"```

```ok so basically find at least two cases where i could have search that doesn't share any words with stuff in my chosen database? that would pass the test?```

```how do i confirm it retrieves without actually building something out first?```

We discussed why the two semantic examples needed testing rather than assuming that an embedding model would always retrieve the intended movie.

## 2. Inspecting real data and building the first database

I provided the downloaded CMU archive and a pasted sample. The assistant inspected
the plot and metadata files and connected them using Wikipedia movie IDs. It ran
an initial semantic-search experiment on 16 pasted movie descriptions.

Important prompts:

```test these movies as a starting subset```

```help me set up my project, including a python virtual environemnt, chromadb, and .gitignore. load the small sample of movies into a vector datbase. ```

```i still don't get why you need to separate the passages for the movies? why not do it in one chunk?```

```does my search need to be semantic? cuz idk how normal users would purposely make it semantic? like was the point of that just to see if databse is even necessary? if it's not natural for users to write like that does that mean the concept of my project is not inherenlty useful?```

```so i can write something like: recommend me a creepy movie that takes place in a rural area" i feel like that describes the what and not reallly meaning so much```

```what about a search like: a light hearted romantic comedy from the early 2000s?```

```this search didn't work that well. it gave me two of the same results as when i asked for a creepy rural setting movie```

```can u use a diff embedding moel that could hold the whole descipritons?```

```is that still under chroma/abiding by assignment requirements?```

```so when i type in what i want to watch, is the metadata filtering happenign separately from the meaning stuff and then the two cojoin or how does it work?```

The assistant created the virtual environment, requirements, ignore rules, loader,
and setup guide. The initial persistent database contained 50 movies split into
140 passages. Restarting and duplicate-loading behavior were checked. An install
attempt ran out of disk space; temporary files from earlier testing were removed
before retrying.

## 3. Adding search and investigating weak results

Important prompts:

```text
ok can u do that? also i still don't get why you need to separate hte passages for the movies
```

```text
does my search need to be semantic? cuz idk how normal users would purposely make it semantic? like was the point of that just to see if databse is even necessary? if it's not natural for users to write like that does that mean the concept of my project is not inherenlty useful?
```

```text
this search ddin't work that well. it gave me two of the same results as when i asked for a creepy rural setting movie
```

```text
can i see my terminal and what each search returned? also why can't we just use the whole passage even though u said therea a wrord limit. itw oudl solve that problem
```

The assistant added a search script and explained that the default model only read
a limited number of tokens per item. I tried ordinary requests about mood and
genre. Results overlapped across different requests, which led to further testing.

The assistant initially placed too much emphasis on the benefits of reading full
plots. Later experiments showed that accepting more text does not automatically
make retrieval more accurate.

## 4. Switching to full plots, expanding the corpus, and adding filters

Important prompts:

```text
use a diff one that could hold the hwole descipriton then
```

```text
ok check what it recommended now for rom com is it better?
```

```text
yes please. also i think you can add more movies now cuz i cleared some storage
```

```text
so when i type in what i want to watch, is the metadata filtering happenign separately from the meaning stuff and then the two cojoin or how does it work?
```

The app changed to Jina full-plot embeddings and expanded to 500 movies. It added
numeric release-year metadata and a romantic-comedy flag. Supported decade phrases
and romantic-comedy requests could then apply exact filters before ranking eligible
movies by vector similarity.

This improved the eligibility of some results, but it did not establish that the
underlying semantic ranking was consistently good. Full plots remained one item
per movie; the loader rejected over-limit inputs instead of silently truncating
them.

## 5. Adding movies during use and testing semantic examples

Important prompt:

```text
can you help me complete the adding new info and two successful searches
```

The assistant added an interactive menu with search, add, and quit actions.
User-added movies received unique IDs, and their plots were embedded immediately.
Tests used a temporary database to check adding, immediate retrieval, quitting,
and retrieval after restarting without changing the real movie collection.

Several proposed semantic searches failed. Two that succeeded were initially
recorded in `semantic_search_results.json`: a firearm-linked anthology query for
*The Gun* and a housebound-witness query for *Frozen with Fear*. We later tested
more natural alternatives for my README rather than treating the first examples
as the only possible choices.

## 6. Adding a persistent watchlist

Important prompts:

```text
i think maybe building a saved watchlist then? alos how do i quit, reopen and confirm it remains if i'm just running it in my terminal?
```

```text
can you confirm it works by testing it and also implement the saved watchlist?
```

The assistant implemented saving selected search results to a JSON watchlist.
Tests checked that entries survived restarting and that saving the same movie ID
again did not duplicate it. The watchlist was kept separate from the searchable
Chroma collection.

## 7. Adding summaries and trailer links after discussing the project direction

Important prompt:

```text
ok i talked to my professor and i think what i wanna do is use maybe some sort of low running LLM to generate summaries of the top 3 recommendations for the user to see. So basically, the database is still embedding the full descriptions (no chunking or anything) so the recs are as accurate as possible, but then what the user sees is summaries so they don't need to read the whole thing. then, i want to use like youtube API for example to provide links to trailers for each of them as well. can you help me implement these new features and as you're implementing, explain what you're doing
```

The assistant set up a portable local Ollama runtime and tested small Qwen models.
The first freely generated summaries changed plot facts. The final display method
instead asks Qwen to select original sentences, validates the returned indices,
and assembles those sentences into a shorter summary.

YouTube Data API v3 searches use a movie title and year to find trailer candidates.
The app shows the video title/channel and labels the result as a candidate. If the
API is unavailable, it supplies a YouTube search link. If the summary model fails,
it displays a labeled excerpt. Successful summaries and trailer results are cached.

API credentials belong in the ignored `.env` file, not in this log or the repo.
The actual application-model prompts are recorded in `recommendation_details.py`;
they are separate from the development prompts quoted here.

## 8. Checking the running program and adding watchlist removal

Important prompts:

```text
check my terminal? i think it's still printing out the full descriptions
```

```text
so the watchlist is saved the whole time? cuz right now the watchlist has some movies from the old verison ith no summarizes and youtue link
```

```text
can you clear the watchlist or give users a way to remove something from the watchlist?
```

There were initial computer-use permission problems. After access worked, the
assistant observed that the old running process was still printing full plots.
Restarting the app was necessary to load updated code. Older watchlist entries
also retained their original fields rather than automatically gaining summaries.

The assistant implemented removing individual watchlist entries. Tests checked
cancellation, persistence of removal, preservation of other entries, and that
removal did not delete movies from the Chroma corpus.

## 9. Investigating recommendation quality and comparing embedding models

Important prompts:

```text
ok small issue. it recommended me novocaine when i asked for a creepy dystopian movie. but i checked the trailer and its action/comedy???
```

```text
still bad even with just dystopian
```

```text
it didn't work for when. iasked for action filled either if u can see in my terminal
```

```text
can you try implementing a diff model?
```

The assistant confirmed that the weak results were not simply a wording problem.
It compared models against the same plots and queries, preserving the original
collection. Nomic improved some examples, and became the active embedding model,
but broad action and dystopian requests remained weak. BGE-M3 through Ollama
rejected a long input during migration, and a small Qwen3 embedding check did not
resolve the problem. Neither became the active model.

The active Nomic implementation uses different task prefixes for documents and
queries. Results of the Jina/Nomic comparison are recorded in
`embedding_comparison.json`, with a reproducible comparison script.

## 10. Testing whether embedding summaries would work better

Important prompts:

```text
could it be that using full descriptions is making it weaker because the meanings get watered down? maybe some way for it to embed the summaries and not the full plots. (so not chunks either as that just completely truncates certain parts).
```

```text
ok so you're gonna test embedding summaries (maybe use am LLM to do this) and see if it's better?
```

The assistant tested a controlled 60-movie pilot using the same Nomic model and
queries for full plots and LLM-selected synopses. Seven invalid summaries were
excluded from both conditions, leaving 53 movies. Short plots could remain
unchanged. Both conditions retrieved a diagnostic expected title in the top three
for six of seven searches, and action recommendations were still poor.

This did not show a clear overall improvement. The live app therefore continues
embedding full plots. The pilot's results and limitations are recorded in
`summary_embedding_comparison.json`. Its diagnostic score is not a general
accuracy measurement across all movies or user requests.

## 11. Understanding the code, writing the README, and choosing natural examples

Important prompts:

```text
ok can you explain how everything (the code actually works now so that I can get that part down
```

```text
can u explain all the  bullet points in the readme cuz i don't really understand. i'll put it into my own words after and write it myself
```

```text
what about verifieid examples such as  the creepy movies and light hearted rom com cuz i think those worked. the ones u gave sound too specific and AI-like
```

```text
maybe something else then htat isn't that similar to the result but isn't as niche as what u suggested earlier
```

```text
does my README look good?
```

```text
uhh idk what to write for why a keyword search would miss them
```

```text
where do i even add the finish setup and limitation? hlep me format. i put the dataset link when i wrote MovieSummaries.tar.gz, no?
```

```text
did you change any of my content? cuz i'm supposed to write it myself but i think you can help with formatting
```

I asked for explanations of metadata, persistence, the data-loading command,
automatic Nomic downloads, and the difference between Nomic, Qwen, Ollama, and
Chroma. I wrote a README draft and requested review and formatting help.

The assistant checked the natural-search alternatives. My exact README query
“Recommend me movies about getting a second chance.” retrieved *Christmas in
Paradise* at #2, while an earlier differently worded query had retrieved it at #1.
The creepy-rural query retrieved *King of the Ants* at #2, with the secluded-farm
part of the plot providing the connection. We discussed why metadata-filtered
romantic-comedy searches were less convincing proof of semantic retrieval.

The assistant initially changed wording as well as formatting in the README.
After I questioned that, it restored my original wording and removed its added
setup/limitations prose, retaining formatting such as spacing, links, and code
blocks. I need to review the final README myself and ensure its factual claims
and setup instructions are accurate.

## 12. Creating this prompt log and remaining submission work

Important prompt:

```text
now i just need a prompt log help me create one
```

When asked for an honest estimate of active time, my response was:

```text
like 8 hours
```

The assistant assembled this draft from the conversation. I should review it,
correct any inaccurate descriptions, and add work done outside the chat or after
this log was created. No unconfirmed completion of the video, portfolio update,
GitHub publication, or submission form is claimed here.
