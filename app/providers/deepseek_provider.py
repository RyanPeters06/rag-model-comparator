from __future__ import annotations

from typing import Callable

from app.providers.base import BaseProvider


class DeepSeekProvider(BaseProvider):
    def __init__(self, model_config: dict):
        super().__init__(model_config)
        base_url = model_config.get("extra_kwargs", {}).get("base_url", "https://api.deepseek.com")
        try:
            import openai
            self._client = openai.OpenAI(api_key=self.api_key, base_url=base_url)
        except ImportError:
            raise ImportError("openai is required: pip install openai")
        self._is_reasoner = self.model_id == "deepseek-reasoner"

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

            in_tok = 0
            out_tok = 0
            in_reasoning = False

            response = self._client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                stream=True,
                stream_options={"include_usage": True},
            )

            for chunk in response:
                if not chunk.choices:
                    if chunk.usage:
                        in_tok = chunk.usage.prompt_tokens
                        out_tok = chunk.usage.completion_tokens
                    continue

                delta = chunk.choices[0].delta

                # DeepSeek R1 reasoning content
                reasoning = getattr(delta, "reasoning_content", None)
                if reasoning:
                    if not in_reasoning:
                        token_callback("\n[Thinking...]\n")
                        in_reasoning = True
                    token_callback(reasoning)

                content = delta.content
                if content:
                    if in_reasoning:
                        token_callback("\n[Answer]\n")
                        in_reasoning = False
                    token_callback(content)

                if chunk.usage:
                    in_tok = chunk.usage.prompt_tokens
                    out_tok = chunk.usage.completion_tokens

            done_callback(in_tok, out_tok)

        except openai.APIError as exc:
            error_callback(f"DeepSeek API error: {exc}")
        except Exception as exc:
            error_callback(f"Error: {exc}")
