"""Retrieval evaluation.

A RAG system is mostly its retriever: if the right passage is not in the context,
no amount of prompting saves the answer. These metrics score retrieval alone,
against a small hand-written question set in eval/questions.yaml where each
question is labelled with the document that should answer it.

    recall@k  fraction of questions whose correct document appears in the top k
    MRR       mean reciprocal rank of the first correct document
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import yaml

from . import config
from .store import VectorStore

log = logging.getLogger(__name__)


def _load(path: Path | None) -> dict:
    path = path or config.EVAL_DIR / "questions.yaml"
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_questions(path: Path | None = None) -> list[dict]:
    return _load(path)["questions"]


def load_unanswerable(path: Path | None = None) -> list[str]:
    return _load(path).get("unanswerable", [])


def evaluate_abstention(store: VectorStore, answerable: list[str], unanswerable: list[str]) -> dict:
    """How often the system correctly refuses, and how often it wrongly refuses."""
    from .rag import should_abstain

    def abstains(question: str) -> bool:
        return should_abstain(question, store, store.search(question, top_k=1))

    caught = [q for q in unanswerable if abstains(q)]
    wrongly_rejected = [q for q in answerable if abstains(q)]
    return {
        "unanswerable_caught": f"{len(caught)}/{len(unanswerable)}",
        "answerable_wrongly_rejected": f"{len(wrongly_rejected)}/{len(answerable)}",
        "missed_unanswerable": [q for q in unanswerable if q not in caught],
        "wrongly_rejected": wrongly_rejected,
    }


def expected_ids(item: dict) -> set[str]:
    """A question may accept several documents when each genuinely states the answer."""
    value = item["expected_doc_id"]
    return set(value) if isinstance(value, list) else {value}


def evaluate_retrieval(
    store: VectorStore, questions: list[dict] | None = None, k_values: tuple[int, ...] = (1, 3, 5)
) -> dict:
    questions = questions or load_questions()
    indexed = {chunk.doc_id for chunk in store.chunks}
    skipped = [q for q in questions if not expected_ids(q) & indexed]
    questions = [q for q in questions if expected_ids(q) & indexed]
    if not questions:
        raise RuntimeError("None of the evaluation questions refer to an indexed document.")
    max_k = max(k_values)

    hits_at_k = {k: 0 for k in k_values}
    section_hits = {k: 0 for k in k_values}
    n_section_labelled = 0
    reciprocal_ranks: list[float] = []
    per_question: list[dict] = []

    for item in questions:
        expected = expected_ids(item)
        results = store.search(item["question"], top_k=max_k)
        retrieved = [hit.chunk.doc_id for hit in results]

        rank = next((i + 1 for i, doc in enumerate(retrieved) if doc in expected), None)
        correct_score = results[rank - 1].score if rank else None

        section_rank = None
        if item.get("expected_section"):
            n_section_labelled += 1
            wanted = item["expected_section"].lower()
            section_rank = next(
                (i + 1 for i, hit in enumerate(results)
                 if hit.chunk.doc_id in expected and wanted in hit.chunk.section.lower()),
                None,
            )
            for k in k_values:
                if section_rank is not None and section_rank <= k:
                    section_hits[k] += 1
        reciprocal_ranks.append(1.0 / rank if rank else 0.0)
        for k in k_values:
            if rank is not None and rank <= k:
                hits_at_k[k] += 1

        per_question.append(
            {
                "question": item["question"],
                "expected": sorted(expected),
                "rank": rank,
                "section_rank": section_rank,
                "top_result": retrieved[0] if retrieved else None,
                "top_score": round(results[0].score, 4) if results else None,
                "correct_score": round(correct_score, 4) if correct_score is not None else None,
            }
        )

    total = len(questions)
    correct_scores = [row["correct_score"] for row in per_question if row["correct_score"] is not None]
    summary = {
        "n_questions": total,
        "n_skipped_not_indexed": len(skipped),
        "embedding_backend": store.embedder.name,
        **{f"recall@{k}": round(hits_at_k[k] / total, 3) for k in k_values},
        "MRR": round(sum(reciprocal_ranks) / total, 3),
        "n_section_labelled": n_section_labelled,
        **{
            f"section@{k}": round(section_hits[k] / n_section_labelled, 3)
            for k in k_values
            if n_section_labelled
        },
        # Lowest score at which a correct document was still retrieved: an upper
        # bound for the abstention threshold on this corpus and backend.
        "min_correct_score": round(min(correct_scores), 4) if correct_scores else None,
    }
    return {"summary": summary, "per_question": per_question}


def save_report(report: dict, path: Path | None = None) -> Path:
    path = path or config.PROJECT_ROOT / "eval" / "report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    return path
