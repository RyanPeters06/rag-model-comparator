from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.config import TOP_K
from app.rag.pdf_processor import Chunk, render_page_as_base64
from app.rag.vector_store import VectorStore

if TYPE_CHECKING:
    from app.rag.embeddings import EmbeddingModel

logger = logging.getLogger(__name__)


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
        if not results:
            return "", []

        parts = ["RELEVANT DOCUMENTATION FROM KNOWLEDGE BASE:\n"]
        citations: list[str] = []

        for chunk, score in results:
            header = f"[Source: {chunk.display_name}, Page {chunk.page_number}]"
            parts.append(f"{header}\n{chunk.text}")
            citations.append(f"{chunk.display_name} p.{chunk.page_number}")

        parts.append("\nUse the above documentation to answer the following question accurately.")
        context = "\n\n".join(parts)
        return context, citations

    def get_page_images(self, results: list[tuple[Chunk, float]], max_images: int = 5) -> list[str]:
        """Render the source pages of retrieved chunks as base64 PNG images."""
        seen: set[tuple[str, int]] = set()
        images: list[str] = []

        for chunk, _ in results:
            if len(images) >= max_images:
                break
            key = (chunk.source_file, chunk.page_number)
            if key in seen:
                continue
            seen.add(key)
            b64 = render_page_as_base64(chunk.source_file, chunk.page_number)
            if b64:
                images.append(b64)
            else:
                logger.warning("Could not render %s page %d", chunk.display_name, chunk.page_number)

        return images
