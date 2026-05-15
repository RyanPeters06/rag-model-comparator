from __future__ import annotations

import base64
from typing import Callable

from app.providers.base import BaseProvider


class GoogleProvider(BaseProvider):
    def __init__(self, model_config: dict):
        super().__init__(model_config)
        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
            self._genai = genai
        except ImportError:
            raise ImportError("google-genai is required: pip install google-genai")

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
            from google.genai import types

            config_kwargs = {}
            if system_context:
                config_kwargs["system_instruction"] = system_context
            config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

            # Build content parts — images first, then the prompt text
            if images:
                parts = []
                for b64 in images:
                    try:
                        parts.append(types.Part.from_bytes(
                            data=base64.b64decode(b64),
                            mime_type="image/png",
                        ))
                    except Exception:
                        pass
                parts.append(prompt)
                contents = parts
            else:
                contents = prompt

            in_tok = 0
            out_tok = 0

            stream = self._client.models.generate_content_stream(
                model=self.model_id,
                contents=contents,
                config=config,
            )

            for chunk in stream:
                try:
                    if chunk.text:
                        token_callback(chunk.text)
                except Exception:
                    pass
                try:
                    if chunk.usage_metadata:
                        in_tok = chunk.usage_metadata.prompt_token_count or in_tok
                        out_tok = chunk.usage_metadata.candidates_token_count or out_tok
                except Exception:
                    pass

            done_callback(in_tok, out_tok)

        except Exception as exc:
            error_callback(f"Google API error: {exc}")
