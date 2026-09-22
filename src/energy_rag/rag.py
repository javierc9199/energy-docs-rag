"""Retrieval-augmented answering with citations and an explicit abstention rule."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from . import config
from .store import Hit, VectorStore
from .text import coverage

log = logging.getLogger(__name__)

# Abstention. An assistant that invents an alarm threshold or an article number is
# worse than one that says "not found", so the system refuses to answer when either
# signal says the corpus does not cover the question:
#
# 1. Term coverage: the fraction of the question's content words that appear
#    anywhere in the corpus. Off-topic questions ("receta del pulpo") share almost
#    no vocabulary with plant documentation. Measured on eval/questions.yaml, every
#    answerable question scores >= 0.60 and 7 of 10 unanswerable ones <= 0.33.
# 2. Similarity: the cosine score of the best chunk. On its own this is a weak
#    signal (off-topic questions reached 0.64 with TF-IDF+SVD, above some correct
#    hits), so it is kept only as a low safety floor.
#
# Near-domain questions built only from in-domain words ("¿qué dice el plan de
# seguridad y salud sobre trabajos en altura?") pass both gates: no lexical signal
# can tell that the corpus lacks that document. Those are the job of the generation
# prompt, which instructs the model to say when the
# excerpts do not contain the answer. `energy-rag evaluate` measures both gates.
MIN_COVERAGE = 0.35
MIN_SCORE = 0.12

ABSTENTION = (
    "No he encontrado información suficiente en los documentos indexados para responder "
    "a esta pregunta."
)


@dataclass
class Answer:
    question: str
    answer: str
    hits: list[Hit] = field(default_factory=list)
    abstained: bool = False
    backend: str = "extractive"

    @property
    def sources(self) -> list[dict]:
        return [
            {
                "n": index,
                "citation": hit.chunk.citation(),
                "doc_id": hit.chunk.doc_id,
                "collection": hit.chunk.collection,
                "section": hit.chunk.section,
                "page": hit.chunk.page,
                "score": round(hit.score, 4),
            }
            for index, hit in enumerate(self.hits, start=1)
        ]


def extractive(hits: list[Hit]) -> str:
    """No-API fallback: return the best passages verbatim, numbered and cited.

    Keeps the project runnable without any API key, and lets retrieval be judged
    on its own without a language model paraphrasing over its mistakes.
    """
    lines = ["Pasajes más relevantes (modo extractivo, sin generación):", ""]
    for index, hit in enumerate(hits, start=1):
        text = hit.chunk.text
        excerpt = text if len(text) <= 600 else text[:600].rsplit(" ", 1)[0] + "…"
        lines.append(f"[{index}] {hit.chunk.citation()}\n{excerpt}\n")
    return "\n".join(lines).strip()


def should_abstain(
    question: str,
    store: VectorStore,
    hits: list[Hit],
    min_score: float = MIN_SCORE,
    min_coverage: float = MIN_COVERAGE,
) -> bool:
    term_coverage = coverage(question, store.vocabulary)
    best = hits[0].score if hits else 0.0
    if term_coverage < min_coverage or best < min_score:
        log.info("Abstaining: coverage %.2f, best score %.3f", term_coverage, best)
        return True
    return False


def ask(
    question: str,
    store: VectorStore,
    top_k: int = config.TOP_K,
    backend: str | None = None,
    min_score: float = MIN_SCORE,
    min_coverage: float = MIN_COVERAGE,
    llm=None,
) -> Answer:
    """Retrieve, decide whether to answer, then generate.

    `llm` lets callers (and tests) inject any LangChain chat model; otherwise the
    model is built from `backend` ("vertex" or "openai").
    """
    backend = backend or config.LLM_BACKEND
    hits = store.search(question, top_k=top_k)

    if should_abstain(question, store, hits, min_score, min_coverage):
        return Answer(question, ABSTENTION, hits=[], abstained=True, backend=backend)

    if backend == "extractive" and llm is None:
        return Answer(question, extractive(hits), hits=hits, backend=backend)

    from .chain import generate, get_llm

    model = llm or get_llm(backend)
    return Answer(question, generate(question, hits, model), hits=hits, backend=backend)
