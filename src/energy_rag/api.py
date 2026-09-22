"""FastAPI service.

    uvicorn energy_rag.api:app --reload

The index is loaded once at startup, not per request.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import config
from .rag import ask
from .store import VectorStore

state: dict = {"store": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        state["store"] = VectorStore.load()
    except FileNotFoundError:
        state["store"] = None  # /health will report it; /ask will 503
    yield
    state.clear()


app = FastAPI(
    title="Energy Docs RAG",
    description="Question answering over solar PV technical documentation and Spanish electricity regulation.",
    version="0.2.0",
    lifespan=lifespan,
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)
    top_k: int = Field(config.TOP_K, ge=1, le=20)
    backend: str | None = Field(None, description="extractive, vertex or openai")


class Source(BaseModel):
    n: int
    citation: str
    doc_id: str
    collection: str
    section: str
    page: int
    score: float


class AskResponse(BaseModel):
    question: str
    answer: str
    abstained: bool
    backend: str
    sources: list[Source]


@app.get("/health")
def health() -> dict:
    store = state.get("store")
    return {
        "status": "ok" if store else "index missing",
        "chunks": len(store.chunks) if store else 0,
        "embedding_backend": store.embedder.name if store else None,
        "llm_backend": config.LLM_BACKEND,
    }


@app.post("/ask", response_model=AskResponse)
def ask_endpoint(request: AskRequest) -> AskResponse:
    store = state.get("store")
    if store is None:
        raise HTTPException(status_code=503, detail="Index not built. Run `energy-rag ingest`.")

    try:
        answer = ask(request.question, store, top_k=request.top_k, backend=request.backend)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:  # missing API key for the selected backend
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return AskResponse(
        question=answer.question,
        answer=answer.answer,
        abstained=answer.abstained,
        backend=answer.backend,
        sources=answer.sources,
    )
