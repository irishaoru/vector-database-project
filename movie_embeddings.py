"""Shared, local long-context embeddings for loading and searching movies."""

from pathlib import Path

import numpy as np
import onnxruntime as ort
from chromadb.api.types import Documents, EmbeddingFunction
from chromadb.utils.embedding_functions import register_embedding_function
from huggingface_hub import hf_hub_download
from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parent
MODEL = "jinaai/jina-embeddings-v2-small-en"
REVISION = "44e7d1d6caec8c883c2d4b207588504d519788d0"
MAX_TOKENS = 8192
CACHE = ROOT / ".cache" / "jina-embeddings-v2-small-en"


@register_embedding_function
class MovieEmbeddingFunction(EmbeddingFunction[Documents]):
    """Use the official mean-pooling ONNX export; never truncate inputs."""

    def __init__(self):
        for filename in ("tokenizer.json", "model-w-mean-pooling.onnx"):
            if not (CACHE / filename).is_file():
                print(f"Downloading {MODEL}: {filename}", flush=True)
                hf_hub_download(MODEL, filename, revision=REVISION,
                                local_dir=str(CACHE))
        self.tokenizer = Tokenizer.from_file(str(CACHE / "tokenizer.json"))
        self.tokenizer.no_padding()
        self.tokenizer.no_truncation()
        options = ort.SessionOptions()
        options.intra_op_num_threads = 4
        self.session = ort.InferenceSession(
            str(CACHE / "model-w-mean-pooling.onnx"), sess_options=options,
            providers=["CPUExecutionProvider"],
        )

    def token_count(self, text):
        return len(self.tokenizer.encode(text).ids)

    def __call__(self, input):
        embeddings = []
        # Process separately to avoid padding every plot to the longest plot.
        for text in input:
            encoded = self.tokenizer.encode(text)
            if len(encoded.ids) > MAX_TOKENS:
                raise ValueError(
                    f"Text contains {len(encoded.ids)} tokens; {MODEL} supports "
                    f"{MAX_TOKENS}. Shorten it or use a larger-context model. "
                    "No text was silently truncated."
                )
            inputs = {
                "input_ids": np.array([encoded.ids], dtype=np.int64),
                "attention_mask": np.array([encoded.attention_mask], dtype=np.int64),
                "token_type_ids": np.array([encoded.type_ids], dtype=np.int64),
            }
            # This particular ONNX export already includes mean pooling.
            vector = self.session.run(None, inputs)[0][0].astype(np.float32)
            vector /= max(float(np.linalg.norm(vector)), 1e-12)
            embeddings.append(vector)
        return embeddings

    @staticmethod
    def name():
        return "movie_jina_v2_small_onnx"

    def get_config(self):
        return {"model": MODEL, "revision": REVISION}

    @staticmethod
    def build_from_config(config):
        if config != {"model": MODEL, "revision": REVISION}:
            raise ValueError("Embedding configuration does not match this model")
        return MovieEmbeddingFunction()

    def default_space(self):
        return "cosine"
