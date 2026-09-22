"""Embedding backends.

* ``vertex`` — Vertex AI text embeddings (default model ``gemini-embedding-001``).
  This is the backend of the full RAG stack. Documents are embedded with the
  ``RETRIEVAL_DOCUMENT`` task type and questions with ``RETRIEVAL_QUERY``, which
  is how the model is meant to be used for search.

Two offline backends are kept for running without Google Cloud:

* ``tfidf`` — a TF-IDF + SVD projection. No model download, deterministic, fast.
  It is what the tests and CI run on.
* ``sentence-transformers`` — a local multilingual model, downloaded on first use.

All three expose the same methods, so the rest of the pipeline does not care.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Protocol

import numpy as np

from . import config


class Embedder(Protocol):
    name: str

    def fit_transform(self, texts: list[str]) -> np.ndarray: ...

    def transform(self, texts: list[str]) -> np.ndarray: ...


def _normalise(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.clip(norms, 1e-12, None)


class TfidfEmbedder:
    """TF-IDF over word and character n-grams, reduced with truncated SVD."""

    name = "tfidf"

    def __init__(self, n_components: int = 256):
        self.n_components = n_components
        self._vectorizer = None
        self._svd = None

    def fit_transform(self, texts: list[str]) -> np.ndarray:
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer

        self._vectorizer = TfidfVectorizer(
            lowercase=True,
            strip_accents="unicode",
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,
        )
        sparse = self._vectorizer.fit_transform(texts)
        components = min(self.n_components, min(sparse.shape) - 1)
        if components < 2:
            return _normalise(np.asarray(sparse.todense(), dtype="float32"))
        self._svd = TruncatedSVD(n_components=components, random_state=42)
        return _normalise(self._svd.fit_transform(sparse).astype("float32"))

    def transform(self, texts: list[str]) -> np.ndarray:
        if self._vectorizer is None:
            raise RuntimeError("Embedder is not fitted")
        sparse = self._vectorizer.transform(texts)
        if self._svd is None:
            return _normalise(np.asarray(sparse.todense(), dtype="float32"))
        return _normalise(self._svd.transform(sparse).astype("float32"))

    def save(self, path: Path) -> None:
        with open(path, "wb") as handle:
            pickle.dump({"vectorizer": self._vectorizer, "svd": self._svd}, handle)

    def load(self, path: Path) -> None:
        with open(path, "rb") as handle:
            state = pickle.load(handle)
        self._vectorizer, self._svd = state["vectorizer"], state["svd"]


class SentenceTransformerEmbedder:
    """Multilingual dense embeddings. Downloads the model on first use."""

    name = "sentence-transformers"

    def __init__(self, model_name: str = config.SENTENCE_TRANSFORMER_MODEL):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def fit_transform(self, texts: list[str]) -> np.ndarray:
        return self.transform(texts)

    def transform(self, texts: list[str]) -> np.ndarray:
        vectors = self.model.encode(texts, batch_size=32, show_progress_bar=False)
        return _normalise(np.asarray(vectors, dtype="float32"))

    def save(self, path: Path) -> None:
        path.write_text(self.model_name, encoding="utf-8")

    def load(self, path: Path) -> None:
        self.model_name = path.read_text(encoding="utf-8").strip()


class VertexEmbedder:
    """Vertex AI embeddings through LangChain (`langchain-google-genai` on the Vertex AI backend).

    Embeddings are computed once at ingestion and stored in the index, so the API
    is called per document chunk when indexing and once per question when searching.
    `client` can be injected (tests use a fake); otherwise it is built on first use
    from GOOGLE_CLOUD_PROJECT and VERTEX_LOCATION.
    """

    name = "vertex"

    def __init__(
        self,
        model: str = config.VERTEX_EMBEDDING_MODEL,
        dimensions: int | None = config.VERTEX_EMBEDDING_DIMENSIONS,
        client=None,
    ):
        self.model = model
        self.dimensions = dimensions
        self._client = client

    @property
    def client(self):
        if self._client is None:
            project = config.require_env("GOOGLE_CLOUD_PROJECT")
            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            self._client = GoogleGenerativeAIEmbeddings(
                model=self.model,
                vertexai=True,
                project=project,
                location=config.VERTEX_LOCATION,
                output_dimensionality=self.dimensions,
            )
        return self._client

    def fit_transform(self, texts: list[str]) -> np.ndarray:
        vectors = self.client.embed_documents(texts, task_type="RETRIEVAL_DOCUMENT")
        return _normalise(np.asarray(vectors, dtype="float32"))

    def transform(self, texts: list[str]) -> np.ndarray:
        vectors = [self.client.embed_query(text, task_type="RETRIEVAL_QUERY") for text in texts]
        return _normalise(np.asarray(vectors, dtype="float32"))

    def save(self, path: Path) -> None:
        path.write_text(json.dumps({"model": self.model, "dimensions": self.dimensions}), encoding="utf-8")

    def load(self, path: Path) -> None:
        state = json.loads(path.read_text(encoding="utf-8"))
        self.model, self.dimensions = state["model"], state["dimensions"]


def get_embedder(backend: str | None = None) -> Embedder:
    backend = backend or config.EMBEDDING_BACKEND
    if backend == "vertex":
        return VertexEmbedder()
    if backend == "tfidf":
        return TfidfEmbedder()
    if backend in ("sentence-transformers", "st"):
        return SentenceTransformerEmbedder()
    raise ValueError(f"Unknown embedding backend: {backend}")
