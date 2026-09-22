"""Load documents and turn them into retrievable chunks.

Three kinds of source are supported, configured in ``config/sources.yaml``:

* ``local``  — a folder of Markdown, text or PDF files (the synthetic plant corpus,
               or your own private documents in ``data/private/``)
* ``remote`` — PDFs downloaded from a URL (public BOE legislation)

Every chunk keeps its document id, title and either its section heading (Markdown)
or its page number (PDF), so an answer can cite "Códigos de alarma SCADA § E101"
instead of an opaque snippet.
"""

from __future__ import annotations

import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import requests
import yaml

from . import config
from .privacy import assert_safe

log = logging.getLogger(__name__)

USER_AGENT = "energy-docs-rag/0.2 (portfolio project)"
SUPPORTED = {".md", ".markdown", ".txt", ".pdf"}
SKIP_FILES = {"readme.md"}


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    text: str
    page: int = 0
    section: str = ""
    collection: str = ""

    def embedding_text(self) -> str:
        """Text that is embedded and searched: the chunk prefixed with its document title.

        A chunk often never names what it belongs to: the revision history of the
        cabling inspection plan does not contain the word "cableado", only its title
        does. Prefixing the title raised recall@1 from 0.82 to 0.89 on the shipped
        evaluation set. The stored `text` stays clean for display.
        """
        return f"{self.title}. {self.text}"

    def citation(self) -> str:
        if self.section:
            return f"{self.title} § {self.section}"
        if self.page:
            return f"{self.title} (p. {self.page})"
        return self.title


# -- text utilities --------------------------------------------------------


def clean(text: str) -> str:
    """Strip page furniture that BOE PDFs repeat on every page, and normalise spaces."""
    text = re.sub(r"BOLET[ÍI]N OFICIAL DEL ESTADO", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"LEGISLACI[ÓO]N CONSOLIDADA", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"P[áa]gina\s+\d+", " ", text)
    text = re.sub(r"cve:\s*\S+", " ", text)
    text = re.sub(r"Verificable en https?://\S+", " ", text)
    text = re.sub(r"-\n(\w)", r"\1", text)  # de-hyphenate across line breaks
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split(text: str, size: int = config.CHUNK_SIZE, overlap: int = config.CHUNK_OVERLAP) -> list[str]:
    """Split on sentence boundaries where possible, with a fixed overlap."""
    if len(text) <= size:
        return [text] if text else []

    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            window = text[start:end]
            boundary = max(window.rfind(". "), window.rfind("; "), window.rfind(" | "))
            if boundary > size * 0.5:
                end = start + boundary + 1
        pieces.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [piece for piece in pieces if piece]


# -- Markdown --------------------------------------------------------------

FRONT_MATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
HEADING = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)


def parse_front_matter(raw: str) -> tuple[dict, str]:
    match = FRONT_MATTER.match(raw)
    if not match:
        return {}, raw
    meta = yaml.safe_load(match.group(1)) or {}
    return meta, raw[match.end():]


def markdown_sections(body: str) -> list[tuple[str, str]]:
    """Split Markdown into (section heading, section text) pairs.

    The heading kept is the deepest one, e.g. "E101 — Fallo de aislamiento DC",
    which is what a user recognises in a citation.
    """
    matches = list(HEADING.finditer(body))
    if not matches:
        return [("", body)]

    sections: list[tuple[str, str]] = []
    if matches[0].start() > 0:
        sections.append(("", body[: matches[0].start()]))
    for current, following in zip(matches, matches[1:] + [None]):
        end = following.start() if following else len(body)
        heading = current.group(2).strip()
        sections.append((heading, body[current.end():end]))
    return sections


def chunk_markdown(path: Path, doc_id: str, collection: str) -> list[Chunk]:
    meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
    h1 = HEADING.search(body)
    title = meta.get("title") or (h1.group(2).strip() if h1 else path.stem)

    chunks: list[Chunk] = []
    for heading, text in markdown_sections(body):
        # Drop blockquote disclaimers and table rule lines before chunking
        text = re.sub(r"^>.*$", " ", text, flags=re.MULTILINE)
        text = re.sub(r"^\|?[-:| ]+\|?$", " ", text, flags=re.MULTILINE)
        text = re.sub(r"\*\*|__|`", "", text)  # Markdown emphasis and code marks
        text = clean(text)
        if heading == title:
            heading = ""
        for piece in split(text):
            if len(piece) < config.MIN_CHUNK_CHARS:
                continue
            # The heading is prepended so retrieval can match on it ("E101", "backtracking")
            content = f"{heading}. {piece}" if heading else piece
            chunks.append(
                Chunk(
                    chunk_id=f"{doc_id}#{len(chunks)}",
                    doc_id=doc_id,
                    title=title,
                    text=content,
                    section=heading,
                    collection=collection,
                )
            )
    return chunks


# -- PDF and plain text ------------------------------------------------------


def pdf_pages(path: Path) -> list[str]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return [page.extract_text() or "" for page in reader.pages]


def chunk_pdf(path: Path, doc_id: str, title: str, collection: str) -> list[Chunk]:
    chunks: list[Chunk] = []
    for page_number, raw_page in enumerate(pdf_pages(path), start=1):
        for piece in split(clean(raw_page)):
            if len(piece) < config.MIN_CHUNK_CHARS:
                continue
            chunks.append(
                Chunk(
                    chunk_id=f"{doc_id}#p{page_number}#{len(chunks)}",
                    doc_id=doc_id,
                    title=title,
                    text=piece,
                    page=page_number,
                    collection=collection,
                )
            )
    return chunks


def chunk_text(path: Path, doc_id: str, collection: str) -> list[Chunk]:
    text = clean(path.read_text(encoding="utf-8", errors="ignore"))
    return [
        Chunk(chunk_id=f"{doc_id}#{i}", doc_id=doc_id, title=path.stem, text=piece, collection=collection)
        for i, piece in enumerate(split(text))
        if len(piece) >= config.MIN_CHUNK_CHARS
    ]


def chunk_file(path: Path, collection: str, doc_id: str | None = None, title: str | None = None) -> list[Chunk]:
    doc_id = doc_id or path.stem
    suffix = path.suffix.lower()
    if suffix in (".md", ".markdown"):
        return chunk_markdown(path, doc_id, collection)
    if suffix == ".pdf":
        return chunk_pdf(path, doc_id, title or path.stem, collection)
    if suffix == ".txt":
        return chunk_text(path, doc_id, collection)
    return []


# -- sources -------------------------------------------------------------------


def load_sources(path: Path | None = None) -> list[dict]:
    path = path or config.SOURCES_FILE
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle)["collections"]


def resolve(path_str: str) -> Path:
    path = Path(path_str).expanduser()
    return path if path.is_absolute() else config.PROJECT_ROOT / path


def ingest_local(folder: Path, collection: str) -> list[Chunk]:
    if not folder.exists():
        log.warning("Folder %s does not exist, skipping collection %s", folder, collection)
        return []
    chunks: list[Chunk] = []
    for path in sorted(folder.rglob("*")):
        if path.suffix.lower() not in SUPPORTED or path.name.lower() in SKIP_FILES:
            continue
        doc_chunks = chunk_file(path, collection)
        log.info("%s -> %d chunks", path.name, len(doc_chunks))
        chunks.extend(doc_chunks)
    return chunks


def download(documents: list[dict], force: bool = False) -> None:
    config.ensure_dirs()
    for document in documents:
        target = config.PDF_DIR / f"{document['id']}.pdf"
        if target.exists() and not force:
            continue
        log.info("Downloading %s", document["title"])
        try:
            response = requests.get(document["url"], headers={"User-Agent": USER_AGENT}, timeout=120)
            response.raise_for_status()
        except requests.RequestException as exc:
            log.error("Could not download %s: %s", document["id"], exc)
            continue
        target.write_bytes(response.content)


def ingest_remote(documents: list[dict], collection: str) -> list[Chunk]:
    download(documents)
    chunks: list[Chunk] = []
    for document in documents:
        path = config.PDF_DIR / f"{document['id']}.pdf"
        if not path.exists():
            log.warning("Skipping %s, not downloaded", document["id"])
            continue
        chunks.extend(chunk_pdf(path, document["id"], document["title"], collection))
    return chunks


def build_corpus(collections: list[str] | None = None, extra_paths: list[Path] | None = None) -> list[Chunk]:
    """Build the chunk list from the configured collections plus any extra folders."""
    corpus: list[Chunk] = []
    for source in load_sources():
        name = source["name"]
        if collections and name not in collections:
            continue
        if source["type"] == "local":
            folder = resolve(source["path"])
            if source.get("private"):
                assert_safe(folder, f"private collection {name!r}")
            corpus.extend(ingest_local(folder, name))
        elif source["type"] == "remote":
            corpus.extend(ingest_remote(source["documents"], name))
        else:
            raise ValueError(f"Unknown source type {source['type']!r} in collection {name}")

    for folder in extra_paths or []:
        # Folders passed on the command line are treated as private by default
        assert_safe(folder, "private documents")
        corpus.extend(ingest_local(folder, collection=f"extra:{folder.name}"))

    if not corpus:
        raise RuntimeError("No chunks produced. Check config/sources.yaml and the paths it points to.")
    return corpus


def chunks_to_records(chunks: list[Chunk]) -> list[dict]:
    return [asdict(chunk) for chunk in chunks]
