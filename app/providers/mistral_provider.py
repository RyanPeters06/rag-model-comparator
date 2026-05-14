from __future__ import annotations

from typing import Callable

from app.providers.base import BaseProvider


class MistralProvider(BaseProvider):
    def __init__(self, model_config: dict):
        super().__init__(model_config)
        try:
            from mistralai import Mistral
            self._client = Mistral(api_key=self.api_key)
        except ImportError:
            raise ImportError("mistralai is required: pip install mistralai")

    def stream_query(
        self,
        prompt: str,
        system_context: str,
        token_callback: Callable[[str], None],
        done_callback: Callable[[int, int], None],
        error_callback: Callable[[str], None],
    ) -> None:
        try:
            messages = []
            if system_context:
                messages.append({"role": "system", "content": system_context})
            messages.append({"role": "user", "content": prompt})

            in_tok = 0
            out_tok = 0

            with self._client.chat.stream(model=self.model_id, messages=messages) as stream:
                for event in stream:
                    try:
                        delta = event.data.choices[0].delta
                        if delta.content:
                            token_callback(delta.content)
                    except (AttributeError, IndexError):
                        pass
                    try:
                        usage = event.data.usage
                        if usage:
                            in_tok = usage.prompt_tokens or 0
                            out_tok = usage.completion_tokens or 0
                    except AttributeError:
                        pass

            done_callback(in_tok, out_tok)

        except Exception as exc:
            error_callback(f"Mistral API error: {exc}")
