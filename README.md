# Vector Database project

### 1. What my app does and why I chose it:

My app is a movie recommender where the user inputs what they want to watch (this could include things like the genre, mood,  or kind of plot) and the app returns the top 3 recommendations based on semantic meanings of the movies embedded in the vector database. The recommendations are condensed into AI generated summaries instead of the full description, making it more user friendly and also comes with a youtube link to the movie's trailer. Finally, users can choose to save any of the movies into their watchlist and also remove any movies they want from the watchlist as well. I chose this concept because it fits the use of a vector database well because you have to infer the meaning of things like "creepy" or "action-packed" and it isn't just a directly lookup. 

### 2. What is stored in the database:

The data comes from the CMU Movie Summary Corpus which is a collection of movie plots and information about those movies. 500 movies were embedded into the database. The database also stores the embedding which are numbers produced by the model to represent the plot's meaning. 

One movie's full plot counts as one database item. Each item has a document (the full plot text that gets embedded), an ID (unique identifier that distinguishes a movie from other entries), and metadata (release year, genres, source, etc)

In the terminal, to add new items, the user chooses option 2 after starting the app and enters its title, optional year and genres, and a plot description. To search, they choose option 1 and describe what they want to watch. The app converts that request into a vector and asks Chroma for similar movie recommendations.

### 3. My two queries from the test above, the items they retrieve, and why a keyword search would miss them

Verified examples:

**Input:** Recommend me a creepy movie that takes place in a rural area.”

**Output:** "King of the Ants" was ranked #2. It's plot talks about kidnapping and torture at a secluded farm. The description aligns with the meaning of something being creepy and farm is infered from "rural area." The description does not use the words "creepy", "rural" or "area."

Why a keyword search would miss them:

**Input:** "Recommend me movies about getting a second chance."

**Output:** "Christmas in Paradise" was ranked #2. The plot talks about a widowed mother and a divorced father trying to develop a new relationship despite painful past experiences. That represents a second chance but the description never uses "second" or "chance."

### 4. How we would obtain and load the data ourselves

The user needs to:

1. Download [MovieSummaries.tar.gz](https://www.cs.cmu.edu/~ark/personas/) from the CMU dataset website.

2. Run:

   ```sh
   python load_movies.py --archive /path/to/MovieSummaries.tar.gz --limit 500
   ```

   in their terminal

3. Start the app

### 5 Which vector database and embedding model used, and whether anything downloads on first run

My app uses:

- ChromaDB to store movie data and vectors, as well as retrieve the similar items to recommend
- Nomic Embed Text v1.5 to convert full plots and searches into vectors
- Qwen2.5 1.5B through Ollama to select original sentences from the plots to create concise summaries for the users.
- YouTube Data API v3 to get the trailer links

The embedding model downloads automatically when needed Ollama and its summary model require their own set up.

### 6. How to run my app:

1. Open the project folder in VS Code and use the terminal to run it locally.

2. Create and activate a Python environment:

   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install the Python packages:

   ```sh
   python -m pip install -r requirements.txt
   ```

   requirements.txt lists the software libraries your code needs, including ChromaDB. This command installs them into .venv.

4. Download the movie dataset and build the database

   Download [MovieSummaries.tar.gz](https://www.cs.cmu.edu/~ark/personas/) from the CMU dataset website. Then run:

   ```sh
   python load_movies.py --archive /path/to/MovieSummaries.tar.gz --limit 500
   ```

   (replace/path/to/ with the file's actual location). This opens the downloaded archive, reads the movie titles, plots, etc, uses the embedding model (Nomic) to turn each plot into numbers, and saves the movies and numbers in a new chroma_store folder inside the project.

5. Set up the local summary model:

   The user has to install Ollama and then download Qwen.(Ollama is the software that runs Qwen on the user's computer) Run:

   ```sh
   ollama pull qwen2.5:1.5b
   ```

6. Set up a YouTube API key:

   Once the key is set up, copy .env.example to .env and enter your key after it says: YOUTUBE_API_KEY

7. Start the app in your main terminal by doing:

   ```sh
   source .venv/bin/activate
   python app.py
   ```

### 7. Summarization of AI usage, with relevant citations:
AI helped with:

- implementing the app step by step 
- explaining how the vector database actually works like what is being embedding, what is doing the retrieval process, how the data is being converted into vectors 
- explain to me how the code works on a high level 
- helped me test out/compare different embedding models to see if a different one would improve recommendation quality (tested several 
and they were all about the same)
- explained the set up to me and helped me install Ollama and download Qwen

Citations: Used Codex GPT-6.1 Sol Light. CMU Dataset used: https://www.cs.cmu.edu/~ark/personas/

### Limitations:
Certain broad searches such as "recommend me a dystopian movie" or "recommend me something that is action-filled" returned results that didn't match the semantic meaning of the input (Ex: the dystopian request returned a bunch of drama/comedy movies).  Different embedding models were tested but they all yielded about the same recommendation quality. I also tried to ask Codex to embed concise summaries of the movies rather than full descriptions in case the meaning got watered down for some of them with long descriptions. The quality of hth results still remained the same. 