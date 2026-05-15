from __future__ import annotations

from typing import Callable

from app.providers.base import BaseProvider
from app.providers.openai_provider import _build_user_content


class GroqProvider(BaseProvider):
    def __init__(self, model_config: dict):
        super().__init__(model_config)
        base_url = model_config.get("extra_kwargs", {}).get("base_url", "https://api.groq.com/openai/v1")
        try:
            import openai
            self._client = openai.OpenAI(api_key=self.api_key, base_url=base_url)
        except ImportError:
            raise ImportError("openai is required: pip install openai")

    def stream_query(
        self,
        prompt: str,
        system_context: str,
        token_callback: Callable[[str], None],
        done_callback: Callable[[int, int], None],
        error_callback: Callable[[str], None],
        images: list[str] | None = None,
    ) -> None:
        try:
            import openai
            messages = []
            if system_context:
                messages.append({"role": "system", "content": system_context})
            messages.append({"role": "user", "content": _build_user_content(prompt, images)})

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

        except openai.APIError as exc:
            error_callback(f"Groq API error: {exc}")
        except Exception as exc:
            error_callback(f"Error: {exc}")
