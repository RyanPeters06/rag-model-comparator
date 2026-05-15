from __future__ import annotations

import json
import logging
import pickle
from pathlib import Path

import numpy as np

from app.config import INDEX_DIR
from app.rag.pdf_processor import Chunk

logger = logging.getLogger(__name__)

_FAISS_INDEX_FILE = "faiss.index"
_CHUNKS_FILE = "chunks.pkl"
_MANIFEST_FILE = "manifest.json"


class VectorStore:
    def __init__(self, index_dir: Path = INDEX_DIR):
        self.index_dir = index_dir
        self.index = None
        self.chunks: list[Chunk] = []
        self._dim = 384

    def build(self, chunks: list[Chunk], vectors: np.ndarray) -> None:
        try:
            import faiss
        except ImportError:
            raise ImportError("faiss-cpu is required: pip install faiss-cpu")
        self.index = faiss.IndexFlatIP(self._dim)
        self.index.add(vectors.astype(np.float32))
        self.chunks = chunks
        logger.info("Built FAISS index with %d chunks", len(chunks))

    def save(self) -> None:
        if self.index is None:
            return
        try:
            import faiss
        except ImportError:
            raise ImportError("faiss-cpu is required: pip install faiss-cpu")
        self.index_dir.mkdir(exist_ok=True)
        faiss.write_index(self.index, str(self.index_dir / _FAISS_INDEX_FILE))
        with open(self.index_dir / _CHUNKS_FILE, "wb") as f:
            pickle.dump(self.chunks, f)
        # Build manifest: unique files with page counts (use display name for UI)
        files: dict[str, set[int]] = {}
        for c in self.chunks:
            files.setdefault(c.source_file, set()).add(c.page_number)
        manifest = [
            {
                "file": Path(full_path).name,
                "pages": max(pages),
                "chunks": sum(1 for c in self.chunks if c.source_file == full_path),
            }
            for full_path, pages in files.items()
        ]
        with open(self.index_dir / _MANIFEST_FILE, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        logger.info("Saved index to %s", self.index_dir)

    def load(self) -> bool:
        index_path = self.index_dir / _FAISS_INDEX_FILE
        chunks_path = self.index_dir / _CHUNKS_FILE
        if not index_path.exists() or not chunks_path.exists():
            return False
        try:
            import faiss
            self.index = faiss.read_index(str(index_path))
            with open(chunks_path, "rb") as f:
                self.chunks = pickle.load(f)
            logger.info("Loaded index: %d chunks", len(self.chunks))
            return True
        except Exception as exc:
            logger.error("Failed to load index: %s", exc)
            self.index = None
            self.chunks = []
            return False

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> list[tuple[Chunk, float]]:
        if self.index is None or self.index.ntotal == 0:
            return []
        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_vector.astype(np.float32), k)
        results = []
        for j, idx in enumerate(indices[0]):
            if idx >= 0:
                results.append((self.chunks[idx], float(scores[0][j])))
        return results

    def get_manifest(self) -> list[dict]:
        manifest_path = self.index_dir / _MANIFEST_FILE
        if not manifest_path.exists():
            return []
        try:
            with open(manifest_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    @property
    def is_ready(self) -> bool:
        return self.index is not None and len(self.chunks) > 0
