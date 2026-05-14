from __future__ import annotations

from app.config import TOP_K
from app.rag.embeddings import EmbeddingModel
from app.rag.pdf_processor import Chunk
from app.rag.vector_store import VectorStore


class Retriever:
    def __init__(self, vector_store: VectorStore, embedding_model: EmbeddingModel):
        self.store = vector_store
        self.embedder = embedding_model

    def retrieve(self, query: str, top_k: int = TOP_K) -> list[tuple[Chunk, float]]:
        if not self.store.is_ready:
            return []
        vec = self.embedder.embed_query(query)
        return self.store.search(vec, top_k)

    def format_context(self, results: list[tuple[Chunk, float]]) -> tuple[str, list[str]]:
        """Return (system_context_block, list_of_citation_strings)."""
        if not results:
            return "", []

        parts = ["RELEVANT DOCUMENTATION FROM KNOWLEDGE BASE:\n"]
        citations: list[str] = []

        for chunk, score in results:
            header = f"[Source: {chunk.source_file}, Page {chunk.page_number}]"
            parts.append(f"{header}\n{chunk.text}")
            citations.append(f"{chunk.source_file} p.{chunk.page_number}")

        parts.append("\nUse the above documentation to answer the following question accurately.")
        context = "\n\n".join(parts)
        return context, citations
