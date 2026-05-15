from __future__ import annotations

from PyQt5.QtCore import QThread, pyqtSignal

from app.rag.pdf_processor import extract_text_by_page, chunk_text
from app.rag.vector_store import VectorStore
from app.config import CHUNK_SIZE, CHUNK_OVERLAP


class IndexWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, pdf_paths: list[str], vector_store: VectorStore):
        super().__init__()
        self._pdf_paths = pdf_paths
        self._vector_store = vector_store

    def run(self):
        try:
            import numpy as np
            # Import lazily inside the thread so the GUI shows before model loads
            from app.rag.embeddings import EmbeddingModel

            all_chunks = []
            for i, path in enumerate(self._pdf_paths):
                name = path.replace("\\", "/").split("/")[-1]
                self.progress.emit(f"Extracting text: {name} ({i+1}/{len(self._pdf_paths)})")
                pages = extract_text_by_page(path)
                if not pages:
                    self.progress.emit(f"  Skipped (no text): {name}")
                    continue
                chunks = chunk_text(pages, source_file=path, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
                all_chunks.extend(chunks)
                self.progress.emit(f"  {len(chunks)} chunks from {len(pages)} pages")

            if not all_chunks:
                self.finished.emit(False, "No text could be extracted from the selected PDFs.")
                return

            self.progress.emit(f"Loading embedding model (first run downloads ~90 MB)...")
            embedding_model = EmbeddingModel.get_instance()

            self.progress.emit(f"Embedding {len(all_chunks)} chunks...")
            texts = [c.text for c in all_chunks]

            batch_size = 64
            all_vectors = []
            for start in range(0, len(texts), batch_size):
                batch = texts[start:start + batch_size]
                vecs = embedding_model.embed(batch)
                all_vectors.append(vecs)
                done = min(start + batch_size, len(texts))
                self.progress.emit(f"  Embedded {done}/{len(texts)} chunks...")

            vectors = np.vstack(all_vectors)

            self.progress.emit("Building FAISS index...")
            self._vector_store.build(all_chunks, vectors)
            self.progress.emit("Saving index to disk...")
            self._vector_store.save()

            self.finished.emit(True, f"Index ready: {len(all_chunks)} chunks from {len(self._pdf_paths)} PDF(s)")

        except Exception as exc:
            import traceback
            detail = traceback.format_exc()
            self.finished.emit(False, f"Indexing failed ({type(exc).__name__}): {exc}\n\n{detail}")
