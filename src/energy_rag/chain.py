"""LangChain integration: the vector store as a LangChain retriever, and an LCEL
chain that answers with numbered citations.

Retrieval and abstention stay in this project's own code (see ``rag.py``), because
they are what the evaluation measures. LangChain is used for what it is good at:
a uniform interface over chat models, so switching from Gemini on Vertex AI to
OpenAI is a configuration change rather than a rewrite.
"""

from __future__ import annotations

from typing import Any

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import Runnable

from . import config
from .store import Hit, VectorStore

SYSTEM_PROMPT = (
    "You are an assistant for engineers working on solar PV plants. Answer only from "
    "the numbered excerpts provided.\n"
    "- Cite every claim with the excerpt number in square brackets, e.g. [2].\n"
    "- Quote set-points, thresholds and alarm codes exactly as written.\n"
    "- If the excerpts do not contain the answer, say so plainly and do not guess.\n"
    "- Answer in the language of the question."
)

PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", "Excerpts:\n\n{context}\n\nQuestion: {question}"),
    ]
)


class VectorStoreRetriever(BaseRetriever):
    """Exposes :class:`VectorStore` through LangChain's retriever interface."""

    store: Any
    top_k: int = config.TOP_K

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        return [hit_to_document(hit) for hit in self.store.search(query, top_k=self.top_k)]


def hit_to_document(hit: Hit) -> Document:
    chunk = hit.chunk
    return Document(
        page_content=chunk.text,
        metadata={
            "citation": chunk.citation(),
            "doc_id": chunk.doc_id,
            "section": chunk.section,
            "page": chunk.page,
            "collection": chunk.collection,
            "score": hit.score,
        },
    )


def format_context(documents: list[Document]) -> str:
    return "\n\n".join(
        f"[{i}] {doc.metadata['citation']}\n{doc.page_content}"
        for i, doc in enumerate(documents, start=1)
    )


def build_chain(llm: BaseChatModel) -> Runnable:
    """LCEL chain: {context, question} -> prompt -> chat model -> string."""
    return PROMPT | llm | StrOutputParser()


def get_llm(backend: str) -> BaseChatModel:
    if backend == "vertex":
        # langchain-google-genai replaces the deprecated ChatVertexAI; vertexai=True keeps
        # the calls on Vertex AI (Google Cloud project, IAM, regional endpoint).
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=config.VERTEX_MODEL,
            vertexai=True,
            project=config.require_env("GOOGLE_CLOUD_PROJECT"),
            location=config.VERTEX_LOCATION,
            temperature=0,
        )
    if backend == "openai":
        from langchain_openai import ChatOpenAI

        config.require_env("OPENAI_API_KEY")
        return ChatOpenAI(model=config.OPENAI_MODEL, temperature=0)
    raise ValueError(f"Unknown LangChain backend: {backend}")


def generate(question: str, hits: list[Hit], llm: BaseChatModel) -> str:
    documents = [hit_to_document(hit) for hit in hits]
    return build_chain(llm).invoke({"context": format_context(documents), "question": question})


def as_retriever(store: VectorStore, top_k: int = config.TOP_K) -> VectorStoreRetriever:
    return VectorStoreRetriever(store=store, top_k=top_k)
