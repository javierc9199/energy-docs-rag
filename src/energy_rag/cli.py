"""Command line entry point.

    energy-rag ingest                         index every collection in config/sources.yaml
    energy-rag ingest --collection plant-docs index one collection (no network needed)
    energy-rag ingest --path ~/docs/private   also index a private folder (never committed)
    energy-rag ask "..."                      query the index
    energy-rag evaluate --detail              score retrieval against eval/questions.yaml
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from . import config, evaluate, ingest
from .privacy import UnsafeLocationError
from .rag import ask
from .store import VectorStore, build_and_save


def _ingest(args) -> None:
    extra = [Path(p).expanduser().resolve() for p in args.path]
    chunks = ingest.build_corpus(collections=args.collection or None, extra_paths=extra)
    store = build_and_save(chunks, backend=args.backend)

    documents = {c.doc_id for c in store.chunks}
    by_collection: dict[str, int] = {}
    for chunk in store.chunks:
        by_collection[chunk.collection] = by_collection.get(chunk.collection, 0) + 1

    print(f"Indexed {len(store.chunks)} chunks from {len(documents)} documents")
    for name, count in sorted(by_collection.items()):
        print(f"  {name:<20} {count} chunks")
    print(f"Index saved to {config.INDEX_DIR}")


def _warn_if_backend_differs(store: VectorStore) -> None:
    if store.embedder.name != config.EMBEDDING_BACKEND:
        print(
            f"Note: the index was built with the {store.embedder.name!r} embeddings, but "
            f"EMBEDDING_BACKEND is {config.EMBEDDING_BACKEND!r}. Searching with the index's "
            "backend; run `energy-rag ingest` to rebuild it with the new one.\n"
        )


def _ask(args) -> None:
    store = VectorStore.load()
    _warn_if_backend_differs(store)
    answer = ask(args.question, store, top_k=args.top_k, backend=args.backend)
    print(answer.answer)
    if answer.sources and not answer.abstained:
        print("\nFuentes:")
        for source in answer.sources:
            print(f"  [{source['n']}] {source['citation']}  (score {source['score']})")


def _evaluate(args) -> None:
    store = VectorStore.load()
    _warn_if_backend_differs(store)
    qpath = Path(args.questions) if args.questions else None
    questions = evaluate.load_questions(qpath)
    report = evaluate.evaluate_retrieval(store, questions)
    answerable = [row["question"] for row in report["per_question"]]
    report["abstention"] = evaluate.evaluate_abstention(store, answerable, evaluate.load_unanswerable(qpath))

    print("Retrieval")
    print(json.dumps(report["summary"], indent=2))
    print("\nAbstention")
    print(json.dumps(report["abstention"], indent=2, ensure_ascii=False))
    if args.detail:
        print()
        for row in report["per_question"]:
            status = f"rank {row['rank']}" if row["rank"] else "MISSED"
            print(f"  {status:<8} {row['question'][:78]}")
    path = evaluate.save_report(report)
    print(f"\nReport written to {path}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="energy-rag")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest", help="Build the vector index")
    p_ingest.add_argument("--collection", action="append", default=[], help="only these collections (repeatable)")
    p_ingest.add_argument("--path", action="append", default=[], help="extra private folder to index (repeatable)")
    p_ingest.add_argument("--backend", default=None, help="vertex, tfidf or sentence-transformers")
    p_ingest.set_defaults(func=_ingest)

    p_ask = sub.add_parser("ask", help="Ask a question")
    p_ask.add_argument("question")
    p_ask.add_argument("--top-k", type=int, default=config.TOP_K)
    p_ask.add_argument("--backend", default=None, help="extractive, vertex or openai")
    p_ask.set_defaults(func=_ask)

    p_eval = sub.add_parser("evaluate", help="Score retrieval against a labelled question set")
    p_eval.add_argument("--questions", default=None, help="YAML file (default eval/questions.yaml)")
    p_eval.add_argument("--detail", action="store_true")
    p_eval.set_defaults(func=_evaluate)

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(message)s",
    )
    try:
        args.func(args)
    except UnsafeLocationError as exc:
        raise SystemExit(f"Privacy check failed. {exc}") from None


if __name__ == "__main__":
    main()
