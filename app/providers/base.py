from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from app.config import get_api_key


class ProviderConfigError(Exception):
    pass


class BaseProvider(ABC):
    def __init__(self, model_config: dict):
        self.model_id = model_config["id"]
        self.model_config = model_config
        self.api_key = get_api_key(model_config["env_key"])
        if not self.api_key:
            raise ProviderConfigError(
                f"API key '{model_config['env_key']}' is not set.\n"
                f"Add it to your .env file and restart the application."
            )

    @abstractmethod
    def stream_query(
        self,
        prompt: str,
        system_context: str,
        token_callback: Callable[[str], None],
        done_callback: Callable[[int, int], None],
        error_callback: Callable[[str], None],
        images: list[str] | None = None,
    ) -> None:
        """Blocking. Runs inside a QThread. All output via callbacks.

        images: list of base64-encoded PNG strings (page images from RAG).
        Vision-capable providers embed them in the user message; others ignore.
        """
