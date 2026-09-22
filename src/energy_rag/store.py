"""Vector store: cosine similarity over normalised embeddings.

FAISS is used when it is installed and the corpus is large enough to benefit;
otherwise a NumPy dot product does the same job exactly. For a few thousand
chunks the difference is not measurable, and the NumPy path keeps the project
installable anywhere.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from . import config
from .embeddings import Embedder, TfidfEmbedder, get_embedder
from .ingest import Chunk
from .privacy import assert_safe
from .text import content_terms

log = logging.getLogger(__name__)


@dataclass
class Hit:
    chunk: Chunk
    score: float


class VectorStore:
    def __init__(self, embedder: Embedder | None = None, use_faiss: bool = True):
        self.embedder = embedder or get_embedder()
        self.use_faiss = use_faiss
        self.chunks: list[Chunk] = []
        self.vectors: np.ndarray | None = None
        self._faiss_index = None
        self._vocabulary: set[str] | None = None

    @property
    def vocabulary(self) -> set[str]:
        """Every content term in the corpus, used by the abstention gate."""
        if self._vocabulary is None:
            self._vocabulary = set()
            for chunk in self.chunks:
                self._vocabulary.update(content_terms(chunk.embedding_text()))
        return self._vocabulary

    # -- building -------------------------------------------------------

    def build(self, chunks: list[Chunk]) -> "VectorStore":
        self.chunks = chunks
        self._vocabulary = None
        self.vectors = self.embedder.fit_transform([chunk.embedding_text() for chunk in chunks])
        self._build_faiss()
        log.info("Indexed %d chunks, dimension %d", len(chunks), self.vectors.shape[1])
        return self

    def _build_faiss(self) -> None:
        self._faiss_index = None
        if not self.use_faiss or self.vectors is None or len(self.chunks) < 1000:
            return
        try:
            import faiss
        except ImportError:
            return
        index = faiss.IndexFlatIP(self.vectors.shape[1])
        index.add(self.vectors)
        self._faiss_index = index
        log.info("Using FAISS index")

    # -- searching ------------------------------------------------------

    def search(self, query: str, top_k: int = config.TOP_K) -> list[Hit]:
        if self.vectors is None or not self.chunks:
            raise RuntimeError("The index is empty. Run `ingest` first.")
        query_vector = self.embedder.transform([query])
        top_k = min(top_k, len(self.chunks))

        if self._faiss_index is not None:
            scores, indices = self._faiss_index.search(query_vector, top_k)
            pairs = zip(indices[0], scores[0])
        else:
            scores = (self.vectors @ query_vector[0]).astype(float)
            order = np.argsort(-scores)[:top_k]
            pairs = ((index, scores[index]) for index in order)

        return [Hit(chunk=self.chunks[int(i)], score=float(s)) for i, s in pairs]

    # -- persistence ----------------------------------------------------

    def save(self, directory: Path | None = None) -> Path:
        directory = directory or config.INDEX_DIR
        directory.mkdir(parents=True, exist_ok=True)
        # The index holds the full text of every chunk; never let Git pick it up.
        assert_safe(directory, "the vector index")
        np.save(directory / "vectors.npy", self.vectors)
        with open(directory / "chunks.json", "w", encoding="utf-8") as handle:
            json.dump([asdict(chunk) for chunk in self.chunks], handle, ensure_ascii=False)
        (directory / "backend.txt").write_text(self.embedder.name, encoding="utf-8")
        self.embedder.save(directory / "embedder.pkl")
        return directory

    @classmethod
    def load(cls, directory: Path | None = None) -> "VectorStore":
        directory = directory or config.INDEX_DIR
        backend = (directory / "backend.txt").read_text(encoding="utf-8").strip()
        embedder = get_embedder(backend)
        embedder.load(directory / "embedder.pkl")

        store = cls(embedder=embedder)
        store.vectors = np.load(directory / "vectors.npy")
        with open(directory / "chunks.json", encoding="utf-8") as handle:
            store.chunks = [Chunk(**record) for record in json.load(handle)]
        store._build_faiss()
        return store


def build_and_save(chunks: list[Chunk], backend: str | None = None) -> VectorStore:
    store = VectorStore(embedder=get_embedder(backend)).build(chunks)
    store.save()
    return store
