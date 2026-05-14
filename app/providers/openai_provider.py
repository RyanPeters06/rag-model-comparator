from __future__ import annotations

from typing import Callable

from app.providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    def __init__(self, model_config: dict):
        super().__init__(model_config)
        try:
            import openai
            self._client = openai.OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai is required: pip install openai")

    def stream_query(
        self,
        prompt: str,
        system_context: str,
        token_callback: Callable[[str], None],
        done_callback: Callable[[int, int], None],
        error_callback: Callable[[str], None],
    ) -> None:
        try:
            import openai
            messages = []
            if system_context:
                messages.append({"role": "system", "content": system_context})
            messages.append({"role": "user", "content": prompt})

            supports_streaming = self.model_config.get("supports_streaming", True)

            if supports_streaming:
                in_tok = 0
                out_tok = 0
                response = self._client.chat.completions.create(
                    model=self.model_id,
                    messages=messages,
                    stream=True,
                    stream_options={"include_usage": True},
                )
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        token_callback(chunk.choices[0].delta.content)
                    if chunk.usage:
                        in_tok = chunk.usage.prompt_tokens
                        out_tok = chunk.usage.completion_tokens
                done_callback(in_tok, out_tok)
            else:
                # Non-streaming fallback (e.g. o4-mini)
                response = self._client.chat.completions.create(
                    model=self.model_id,
                    messages=messages,
                )
                content = response.choices[0].message.content or ""
                token_callback(content)
                in_tok = response.usage.prompt_tokens if response.usage else 0
                out_tok = response.usage.completion_tokens if response.usage else 0
                done_callback(in_tok, out_tok)

        except openai.APIError as exc:
            error_callback(f"OpenAI API error: {exc}")
        except Exception as exc:
            error_callback(f"Error: {exc}")
