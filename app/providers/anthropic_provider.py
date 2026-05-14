from __future__ import annotations

from typing import Callable

from app.providers.base import BaseProvider


class AnthropicProvider(BaseProvider):
    def __init__(self, model_config: dict):
        super().__init__(model_config)
        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic is required: pip install anthropic")

    def stream_query(
        self,
        prompt: str,
        system_context: str,
        token_callback: Callable[[str], None],
        done_callback: Callable[[int, int], None],
        error_callback: Callable[[str], None],
    ) -> None:
        try:
            import anthropic
            messages = [{"role": "user", "content": prompt}]
            kwargs = {
                "model": self.model_id,
                "max_tokens": 4096,
                "messages": messages,
            }
            if system_context:
                kwargs["system"] = system_context

            with self._client.messages.stream(**kwargs) as stream:
                for text in stream.text_stream:
                    token_callback(text)
                final = stream.get_final_message()
                in_tok = final.usage.input_tokens
                out_tok = final.usage.output_tokens

            done_callback(in_tok, out_tok)
        except anthropic.APIError as exc:
            error_callback(f"Anthropic API error: {exc}")
        except Exception as exc:
            error_callback(f"Error: {exc}")
