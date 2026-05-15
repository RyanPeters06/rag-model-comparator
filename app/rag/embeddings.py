from __future__ import annotations

import numpy as np
from app.config import EMBEDDING_MODEL


class EmbeddingModel:
    _instance: "EmbeddingModel | None" = None

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        try:
            from fastembed import TextEmbedding
            self._model = TextEmbedding(model_name=f"sentence-transformers/{model_name}")
        except ImportError:
            raise ImportError("fastembed is required: pip install fastembed")
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load embedding model ({type(exc).__name__}): {exc}\n"
                "Tip: restart the app — onnxruntime DLLs must load before Qt on Windows."
            ) from exc

    @classmethod
    def get_instance(cls) -> "EmbeddingModel":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 384), dtype=np.float32)
        vectors = np.array(list(self._model.embed(texts)), dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / np.maximum(norms, 1e-10)

    def embed_query(self, query: str) -> np.ndarray:
        return self.embed([query])
