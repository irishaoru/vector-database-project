"""Local Nomic embeddings with separate document/query task prefixes."""

from pathlib import Path

import numpy as np
import onnxruntime as ort
from chromadb.api.types import Documents, EmbeddingFunction
from chromadb.utils.embedding_functions import register_embedding_function
from huggingface_hub import hf_hub_download
from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parent
MODEL = "nomic-ai/nomic-embed-text-v1.5"
REVISION = "e9b6763023c676ca8431644204f50c2b100d9aab"
MAX_TOKENS = 8192
CACHE = ROOT / ".cache" / "nomic-embed-text-v1.5"


@register_embedding_function
class NomicEmbeddingFunction(EmbeddingFunction[Documents]):
    def __init__(self):
        for filename in ("tokenizer.json", "onnx/model_quantized.onnx"):
            if not (CACHE / filename).is_file():
                print(f"Downloading {MODEL}: {filename}", flush=True)
                hf_hub_download(MODEL, filename, revision=REVISION, local_dir=str(CACHE))
        self.tokenizer = Tokenizer.from_file(str(CACHE / "tokenizer.json"))
        self.tokenizer.no_padding()
        self.tokenizer.no_truncation()
        options = ort.SessionOptions()
        options.intra_op_num_threads = 4
        self.session = ort.InferenceSession(str(CACHE / "onnx/model_quantized.onnx"),
            sess_options=options, providers=["CPUExecutionProvider"])

    def token_count(self, text):
        return len(self.tokenizer.encode("search_document: " + text).ids)

    def _embed(self, texts, prefix):
        embeddings = []
        for text in texts:
            encoded = self.tokenizer.encode(prefix + text)
            if len(encoded.ids) > MAX_TOKENS:
                raise ValueError(f"Text has {len(encoded.ids)} tokens including the task prefix; "
                                 f"the model limit is {MAX_TOKENS}. Nothing was truncated.")
            inputs = {"input_ids": np.array([encoded.ids], dtype=np.int64),
                      "attention_mask": np.array([encoded.attention_mask], dtype=np.int64),
                      "token_type_ids": np.array([encoded.type_ids], dtype=np.int64)}
            tokens = self.session.run(None, inputs)[0]
            mask = inputs["attention_mask"][..., None]
            # The ONNX export returns token vectors, so pool all non-padding tokens.
            vector = ((tokens * mask).sum(axis=1) / mask.sum(axis=1))[0].astype(np.float32)
            # Layer normalization followed by L2 normalization, as documented
            # by Nomic. The variance scale cancels during L2 normalization.
            vector -= vector.mean()
            vector /= max(float(np.linalg.norm(vector)), 1e-12)
            embeddings.append(vector)
        return embeddings

    def __call__(self, input):
        return self._embed(input, "search_document: ")

    def embed_query(self, input):
        return self._embed(input, "search_query: ")

    @staticmethod
    def name():
        return "movie_nomic_v15_onnx"

    def get_config(self):
        return {"model": MODEL, "revision": REVISION}

    @staticmethod
    def build_from_config(config):
        if config != {"model": MODEL, "revision": REVISION}:
            raise ValueError("Embedding configuration does not match this model")
        return NomicEmbeddingFunction()

    def default_space(self):
        return "cosine"
