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

## 2. Inspecting real data and building the actual vector database

I provided the downloaded CMU archive and a pasted sample. The assistant inspected the plot and metadata files and connected them using Wikipedia movie IDs. It ran
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

```i think maybe building a saved watchlist then? alos how do i quit, reopen and confirm it remains if i'm just running it in my terminal?```
```can you confirm it works by testing it and also implement the saved watchlist?```

```ok can you explain how everything (the code actually works now so that I can get that part down```

The assistant created the virtual environment, requirements, ignore rules, loader, and setup guide. The initial persistent database contained 50 movies split into 140 passages because the install attempt ran out of disk space. A later iteration included 500 movies instead which also helped with result quality. 

### 3. Implementation of new features:
```ok i talked to my professor and i think what i wanna do is use maybe some sort of low running LLM to generate summaries of the top 3 recommendations for the user to see. So basically, the database is still embedding the full descriptions (no chunking or anything) so the recs are as accurate as possible, but then what the user sees is summaries so they don't need to read the whole thing. then, i want to use like youtube API for example to provide links to trailers for each of them as well. can you help me implement these new features and as you're implementing, explain what you're doing```

```check my terminal? i think it's still printing out the full descriptions```

```so the watchlist is saved the whole time? cuz right now the watchlist has some movies from the old verison ith no summarizes and youtue link```

```can you clear the watchlist or give users a way to remove something from the watchlist?```

The assistant set up a portable local Ollama runtime and tested small Qwen models. YouTube Data API v3 searches use a movie title and year to find trailer candidates. The app shows the video title/channel and labels the result as a candidate. If the API is unavailable, it supplies a YouTube search link. If the summary model fails, it displays a labeled excerpt. Successful summaries and trailer results are cached.

## 4. Adding search and investigating weak results
 
Important prompts:

```ok small issue. it recommended me novocaine when i asked for a creepy dystopian movie. but i checked the trailer and its action/comedy???```

```so try a prompt with just dystopian and no creepy? are you saying it just based it off the first satisfcation and din't bother to check for dystopian once creepy was satisfied?```

```still bad even with just dystopian```

```can you try implementing a diff embedding model?```

```could it be that using full descriptions is making it weaker because the meanings get watered down? maybe some way for it to embed the summaries and not the full plots. (so not chunks either as that just completely truncates certain parts).```

We tried experimenting with different reasons as to way the search results weren't very accurate in some cases. Ultimately didn't reach a conclusion in time but tried to isolate what we were searching for (so just used that one adjective, "dystopian"), use a different embedding model, and use summaries instead of full descriptions.
