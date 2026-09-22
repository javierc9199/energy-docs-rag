"""Configuration. Secrets come from the environment, never from the repository."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Settings can live in a .env file at the project root (see .env.example).
# Variables already set in the environment take precedence.
try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env", override=False)
except ImportError:  # python-dotenv is optional at runtime
    pass
CONFIG_DIR = PROJECT_ROOT / "config"
CORPUS_DIR = PROJECT_ROOT / "corpus"
DATA_DIR = PROJECT_ROOT / "data"
PDF_DIR = DATA_DIR / "pdf"
PRIVATE_DIR = DATA_DIR / "private"  # git-ignored: put your own documents here
INDEX_DIR = Path(os.environ.get("INDEX_DIR", DATA_DIR / "index"))
EVAL_DIR = PROJECT_ROOT / "eval"

SOURCES_FILE = CONFIG_DIR / "sources.yaml"

# Chunking: ~1,200 characters keeps a procedure step or a legal article mostly
# intact; the overlap stops a definition being split from the clause that uses it.
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
MIN_CHUNK_CHARS = 80

# Retrieval
TOP_K = 5

# Embedding backend:
#   vertex                 Vertex AI text embeddings (the full RAG stack, needs Google Cloud)
#   tfidf                  TF-IDF + SVD, offline and deterministic (default, used in tests and CI)
#   sentence-transformers  local multilingual model, downloaded on first use
EMBEDDING_BACKEND = os.environ.get("EMBEDDING_BACKEND", "tfidf")
VERTEX_EMBEDDING_MODEL = os.environ.get("VERTEX_EMBEDDING_MODEL", "gemini-embedding-001")
# gemini-embedding-001 returns 3,072 dimensions by default and supports truncation;
# 768 keeps the index small with little loss for a corpus of this size.
VERTEX_EMBEDDING_DIMENSIONS = int(os.environ.get("VERTEX_EMBEDDING_DIMENSIONS", "768"))
SENTENCE_TRANSFORMER_MODEL = os.environ.get(
    "SENTENCE_TRANSFORMER_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# Generation backend:
#   extractive  no API key, returns the retrieved passages with citations
#   vertex      Gemini on Google Cloud Vertex AI, through LangChain
#   openai      OpenAI chat models, through LangChain
LLM_BACKEND = os.environ.get("LLM_BACKEND", "extractive")
# Model IDs change as Google retires versions; override with the env var if this one is gone.
VERTEX_MODEL = os.environ.get("VERTEX_MODEL", "gemini-2.5-flash")
VERTEX_LOCATION = os.environ.get("VERTEX_LOCATION", "europe-west1")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is not set. Export it or add it to your .env file.")
    return value


def ensure_dirs() -> None:
    for path in (PDF_DIR, PRIVATE_DIR, INDEX_DIR):
        path.mkdir(parents=True, exist_ok=True)
