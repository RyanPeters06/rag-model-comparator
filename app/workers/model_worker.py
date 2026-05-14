from __future__ import annotations

import time

from PyQt5.QtCore import QThread, pyqtSignal

from app.cost_tracker import calculate_cost
from app.providers.base import ProviderConfigError


_PROVIDER_CLASS_MAP: dict[str, type] = {}


def _get_provider_class(class_name: str):
    if class_name not in _PROVIDER_CLASS_MAP:
        if class_name == "AnthropicProvider":
            from app.providers.anthropic_provider import AnthropicProvider
            _PROVIDER_CLASS_MAP[class_name] = AnthropicProvider
        elif class_name == "OpenAIProvider":
            from app.providers.openai_provider import OpenAIProvider
            _PROVIDER_CLASS_MAP[class_name] = OpenAIProvider
        elif class_name == "GoogleProvider":
            from app.providers.google_provider import GoogleProvider
            _PROVIDER_CLASS_MAP[class_name] = GoogleProvider
        elif class_name == "DeepSeekProvider":
            from app.providers.deepseek_provider import DeepSeekProvider
            _PROVIDER_CLASS_MAP[class_name] = DeepSeekProvider
        elif class_name == "MistralProvider":
            from app.providers.mistral_provider import MistralProvider
            _PROVIDER_CLASS_MAP[class_name] = MistralProvider
        elif class_name == "XAIProvider":
            from app.providers.xai_provider import XAIProvider
            _PROVIDER_CLASS_MAP[class_name] = XAIProvider
        elif class_name == "OpenRouterProvider":
            from app.providers.openrouter_provider import OpenRouterProvider
            _PROVIDER_CLASS_MAP[class_name] = OpenRouterProvider
        else:
            raise ValueError(f"Unknown provider class: {class_name}")
    return _PROVIDER_CLASS_MAP[class_name]


class ModelWorker(QThread):
    token_received = pyqtSignal(str)
    finished = pyqtSignal(int, int, float, float)  # in_tok, out_tok, elapsed, cost_usd
    error_occurred = pyqtSignal(str)

    def __init__(self, model_config: dict, prompt: str, system_context: str):
        super().__init__()
        self._model_config = model_config
        self._prompt = prompt
        self._system_context = system_context
        self._start_time = 0.0

    def run(self):
        self._start_time = time.time()
        try:
            cls = _get_provider_class(self._model_config["provider_class"])
            provider = cls(self._model_config)
        except ProviderConfigError as exc:
            self.error_occurred.emit(str(exc))
            return
        except ImportError as exc:
            self.error_occurred.emit(str(exc))
            return
        except Exception as exc:
            self.error_occurred.emit(f"Failed to initialize provider: {exc}")
            return

        provider.stream_query(
            prompt=self._prompt,
            system_context=self._system_context,
            token_callback=lambda tok: self.token_received.emit(tok),
            done_callback=self._on_done,
            error_callback=lambda msg: self.error_occurred.emit(msg),
        )

    def _on_done(self, in_tokens: int, out_tokens: int):
        elapsed = time.time() - self._start_time
        cost = calculate_cost(self._model_config["id"], in_tokens, out_tokens)
        self.finished.emit(in_tokens, out_tokens, elapsed, cost)
