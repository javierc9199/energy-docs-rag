"""Tests: no network, no API keys. The synthetic plant corpus ships with the repo."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from energy_rag import config, evaluate, rag
from energy_rag.ingest import Chunk, chunk_markdown, clean, ingest_local, markdown_sections, split
from energy_rag.privacy import UnsafeLocationError, assert_safe
from energy_rag.store import VectorStore
from energy_rag.text import content_terms, coverage

CORPUS = config.CORPUS_DIR / "planta-los-almendros"


@pytest.fixture(scope="module")
def store() -> VectorStore:
    # Offline backend on purpose: tests never call Google Cloud, whatever .env says.
    from energy_rag.embeddings import get_embedder

    return VectorStore(embedder=get_embedder("tfidf")).build(ingest_local(CORPUS, collection="plant-docs"))


# -- ingestion ---------------------------------------------------------------


def test_clean_strips_boe_page_furniture():
    raw = "BOLETÍN OFICIAL DEL ESTADO\nLEGISLACIÓN CONSOLIDADA\nPágina 12\ncve: BOE-A-2019-5089\nTexto útil."
    assert clean(raw) == "Texto útil."


def test_split_respects_size_and_overlaps():
    text = ". ".join(f"Frase número {i} con contenido suficiente" for i in range(60))
    pieces = split(text, size=300, overlap=60)
    assert len(pieces) > 1
    assert all(len(piece) <= 340 for piece in pieces)
    tail_words = [w for w in pieces[0][-40:].split() if len(w) > 4]
    assert any(word in pieces[1] for word in tail_words)


def test_markdown_is_split_by_section_with_front_matter_title():
    chunks = chunk_markdown(CORPUS / "5-operacion-y-mantenimiento" / "03-codigos-alarma-scada.md", "alarms", "plant-docs")
    sections = {chunk.section for chunk in chunks}

    assert chunks[0].title == "Códigos de alarma SCADA — Inversores y seguidores"
    assert "E101 — Fallo de aislamiento DC" in sections
    e101 = next(c for c in chunks if c.section.startswith("E101"))
    assert "50 kΩ" in e101.text
    assert e101.citation() == "Códigos de alarma SCADA — Inversores y seguidores § E101 — Fallo de aislamiento DC"


def test_disclaimer_blockquotes_are_not_indexed():
    chunks = chunk_markdown(CORPUS / "5-operacion-y-mantenimiento" / "01-manual-om.md", "om", "plant-docs")
    assert not any("Documento ficticio" in chunk.text for chunk in chunks)


def test_markdown_sections_handles_text_without_headings():
    assert markdown_sections("solo texto") == [("", "solo texto")]


def test_every_synthetic_document_is_indexed(store):
    expected = {p.stem for p in CORPUS.rglob("*.md")}
    assert len(expected) == 17
    assert {chunk.doc_id for chunk in store.chunks} == expected


# -- retrieval ---------------------------------------------------------------


@pytest.mark.parametrize(
    "question, doc_id",
    [
        ("¿Qué hago si el inversor da fallo de aislamiento con rocío?", "03-codigos-alarma-scada"),
        ("¿Por qué se fundían los fusibles del bloque 12?", "07-informe-incidencia-2024-03"),
        ("¿Qué rampa de potencia aplica el controlador de planta?", "09-requisitos-conexion-red"),
        ("¿Qué tolerancia de verticalidad tienen los perfiles hincados?", "14-procedimiento-hincado-pilotes"),
        ("¿Qué es un punto de parada del PPI?", "15-ppi-hincado-montaje-estructura"),
        ("¿Qué autorizaciones administrativas necesita la planta?", "12-proyecto-tecnico-administrativo"),
    ],
)
def test_retrieval_finds_the_right_document(store, question, doc_id):
    assert store.search(question, top_k=1)[0].chunk.doc_id == doc_id


def test_title_prefix_finds_chunks_that_never_name_their_document(store):
    # The revision history of PPI-05 never says "cableado"; only the document title does.
    hits = store.search("¿Qué cambió en la revisión 2 del PPI de cableado?", top_k=5)
    assert "16-ppi-zanjas-cableado" in [hit.chunk.doc_id for hit in hits]


def test_embedding_text_is_prefixed_with_title_but_display_text_is_not():
    chunk = Chunk(chunk_id="x#0", doc_id="x", title="PPI-05", text="Rev. 2: cambios")
    assert chunk.embedding_text() == "PPI-05. Rev. 2: cambios"
    assert chunk.text == "Rev. 2: cambios"


def test_index_survives_a_save_and_load_cycle(store, tmp_path):
    store.save(tmp_path)
    reloaded = VectorStore.load(tmp_path)
    question = "garantías y rendimiento del inversor"
    assert len(reloaded.chunks) == len(store.chunks)
    assert reloaded.search(question, 1)[0].chunk.chunk_id == store.search(question, 1)[0].chunk.chunk_id
    assert reloaded.chunks[0].section == store.chunks[0].section


# -- answering and abstention ---------------------------------------------------


def test_extractive_answer_carries_section_citations(store):
    answer = rag.ask("¿Con qué viento van los seguidores a posición de defensa?", store, backend="extractive")
    assert not answer.abstained
    assert "[1]" in answer.answer
    assert any("§" in source["citation"] for source in answer.sources)


def test_abstains_on_off_topic_question(store):
    answer = rag.ask("¿Cuál es la receta del pulpo a la gallega?", store, backend="extractive")
    assert answer.abstained
    assert answer.answer == rag.ABSTENTION
    assert answer.sources == []


def test_coverage_separates_domain_from_off_topic(store):
    assert coverage("¿Cada cuánto se engrasan los rodamientos de los seguidores?", store.vocabulary) > 0.6
    assert coverage("¿Quién ganó la liga de fútbol?", store.vocabulary) == 0.0


def test_content_terms_ignores_stopwords_and_folds_plurals():
    assert content_terms("¿Cuáles son los seguidores de la planta?") == ["seguidor", "planta"]


# -- LangChain -----------------------------------------------------------------


def test_langchain_chain_receives_numbered_context(store):
    from langchain_core.language_models.fake_chat_models import FakeListChatModel

    llm = FakeListChatModel(responses=["La posición de defensa se activa por encima de 60 km/h [1]."])
    answer = rag.ask("¿Con qué viento van los seguidores a defensa?", store, backend="vertex", llm=llm)

    assert answer.answer.endswith("[1].")
    assert answer.backend == "vertex"
    assert not answer.abstained


def test_langchain_retriever_returns_documents_with_citations(store):
    from energy_rag.chain import as_retriever

    documents = as_retriever(store, top_k=2).invoke("fallo de ventilador del inversor")
    assert len(documents) == 2
    assert documents[0].metadata["citation"]
    assert documents[0].metadata["collection"] == "plant-docs"


def test_prompt_formats_context_with_citation_numbers(store):
    from energy_rag.chain import PROMPT, format_context, hit_to_document

    docs = [hit_to_document(hit) for hit in store.search("limpieza de módulos", top_k=2)]
    messages = PROMPT.format_messages(context=format_context(docs), question="¿Cuándo se limpia?")
    assert "[1]" in messages[1].content and "[2]" in messages[1].content
    assert "do not guess" in messages[0].content


# -- evaluation ------------------------------------------------------------------


def test_evaluation_accepts_multiple_valid_documents(store):
    questions = [
        {"question": "¿A qué viento se protegen los seguidores?",
         "expected_doc_id": ["04-mantenimiento-seguidores", "03-codigos-alarma-scada"]},
        {"question": "¿Quién aprueba el autoconsumo?", "expected_doc_id": "rd-244-2019"},  # not indexed
    ]
    report = evaluate.evaluate_retrieval(store, questions)
    assert report["summary"]["n_questions"] == 1
    assert report["summary"]["n_skipped_not_indexed"] == 1
    assert report["summary"]["recall@3"] == 1.0


def test_shipped_evaluation_meets_a_floor(store):
    """Guards against regressions in chunking or retrieval."""
    report = evaluate.evaluate_retrieval(store)
    assert report["summary"]["recall@3"] >= 0.9
    abstention = evaluate.evaluate_abstention(
        store, [row["question"] for row in report["per_question"]], evaluate.load_unanswerable()
    )
    assert abstention["answerable_wrongly_rejected"].startswith("0/")


# -- privacy -----------------------------------------------------------------------


@pytest.fixture
def git_repo(tmp_path) -> Path:
    if shutil.which("git") is None:
        pytest.skip("git not installed")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text("data/\n")
    return tmp_path


def test_privacy_guard_refuses_tracked_location(git_repo):
    tracked = git_repo / "exports"
    tracked.mkdir()
    with pytest.raises(UnsafeLocationError):
        assert_safe(tracked, "the vector index")


def test_privacy_guard_allows_ignored_location(git_repo):
    ignored = git_repo / "data" / "index"
    ignored.mkdir(parents=True)
    assert_safe(ignored, "the vector index")  # does not raise


def test_saving_an_index_into_a_tracked_folder_is_refused(store, git_repo):
    with pytest.raises(UnsafeLocationError):
        store.save(git_repo / "index-in-the-open")


def test_chunk_records_are_backwards_compatible():
    chunk = Chunk(chunk_id="x#0", doc_id="x", title="Doc", text="texto", page=3)
    assert chunk.citation() == "Doc (p. 3)"


# -- Vertex AI embeddings (fake client: no network, no credentials) -------------


class FakeVertexClient:
    """Stands in for GoogleGenerativeAIEmbeddings and records how it was called."""

    def __init__(self):
        from sklearn.feature_extraction.text import HashingVectorizer

        self._vectorizer = HashingVectorizer(n_features=768, strip_accents="unicode", alternate_sign=False)
        self.calls: list[tuple[str, str]] = []

    def embed_documents(self, texts, task_type=None):
        self.calls.append(("documents", task_type))
        return self._vectorizer.transform(texts).toarray().tolist()

    def embed_query(self, text, task_type=None):
        self.calls.append(("query", task_type))
        return self._vectorizer.transform([text]).toarray()[0].tolist()


@pytest.fixture(scope="module")
def vertex_store():
    from energy_rag.embeddings import VertexEmbedder

    embedder = VertexEmbedder(client=FakeVertexClient())
    return VectorStore(embedder=embedder).build(ingest_local(CORPUS, collection="plant-docs"))


def test_vertex_backend_uses_retrieval_task_types(vertex_store):
    vertex_store.search("tolerancia de verticalidad de los perfiles", top_k=1)
    calls = vertex_store.embedder._client.calls
    assert ("documents", "RETRIEVAL_DOCUMENT") in calls
    assert ("query", "RETRIEVAL_QUERY") in calls


def test_vertex_backend_runs_the_full_rag(vertex_store):
    answer = rag.ask("¿Qué tolerancia de verticalidad se admite en los perfiles hincados?", vertex_store,
                     backend="extractive")
    assert not answer.abstained
    assert answer.sources[0]["doc_id"] == "14-procedimiento-hincado-pilotes"


def test_vertex_index_reloads_with_its_model_settings(vertex_store, tmp_path):
    vertex_store.save(tmp_path)
    reloaded = VectorStore.load(tmp_path)

    assert reloaded.embedder.name == "vertex"
    assert reloaded.embedder.model == config.VERTEX_EMBEDDING_MODEL
    assert reloaded.embedder.dimensions == config.VERTEX_EMBEDDING_DIMENSIONS
    reloaded.embedder._client = FakeVertexClient()  # no credentials in tests
    question = "¿Qué es un punto de parada del PPI?"
    assert reloaded.search(question, 1)[0].chunk.chunk_id == vertex_store.search(question, 1)[0].chunk.chunk_id


def test_vertex_backend_requires_a_google_cloud_project(monkeypatch):
    from energy_rag.embeddings import VertexEmbedder

    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    with pytest.raises(RuntimeError, match="GOOGLE_CLOUD_PROJECT"):
        VertexEmbedder().client
