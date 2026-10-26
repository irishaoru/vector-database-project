"""Compare the old and active models on the same corpus without metadata filters."""

import json
import chromadb
from legacy_jina_embeddings import MovieEmbeddingFunction as JinaEmbeddingFunction
from movie_embeddings import MovieEmbeddingFunction, MODEL, REVISION
from load_movies import COLLECTION, ROOT, STORE
from search_movies import search_movies

QUERIES = [
    'a dystopian movie', 'a creepy dystopian movie', 'an action filled movie',
    'a light hearted romantic comedy',
    'Teenagers are forced by a totalitarian government to fight to the death for public entertainment.',
    'An anthology connecting unrelated lives through the same firearm.',
    'A housebound woman fears she imagined a homicide because nobody can verify her account.',
]


def main():
    client = chromadb.PersistentClient(path=str(STORE))
    old = client.get_collection('movie_full_plots_jina_v2', embedding_function=JinaEmbeddingFunction())
    new = client.get_collection(COLLECTION, embedding_function=MovieEmbeddingFunction())
    before = old.get(include=['documents'])
    after = new.get(include=['documents'])
    if dict(zip(before['ids'], before['documents'])) != dict(zip(after['ids'], after['documents'])):
        raise SystemExit('Collections differ. Run rebuild_embeddings.py to compare the same movies.')
    report = {'movie_count': new.count(), 'model': MODEL, 'revision': REVISION,
              'metadata_filters_used': False, 'queries': []}
    for query in QUERIES:
        row = {'query': query}
        for name, collection in [('jina', old), ('nomic', new)]:
            matches = search_movies(collection, query, limit=collection.count())
            row[name] = {
                'top_3': [m['metadata']['title'] for m in matches[:3]],
                'hunger_games_rank': next((i for i, m in enumerate(matches, 1)
                    if m['metadata']['title'] == 'The Hunger Games'), None),
            }
        report['queries'].append(row)
        print(json.dumps(row), flush=True)
    (ROOT / 'embedding_comparison.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
