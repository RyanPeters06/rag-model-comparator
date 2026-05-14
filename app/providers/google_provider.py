from __future__ import annotations

from typing import Callable

from app.providers.base import BaseProvider


class GoogleProvider(BaseProvider):
    def __init__(self, model_config: dict):
        super().__init__(model_config)
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._genai = genai
        except ImportError:
            raise ImportError("google-generativeai is required: pip install google-generativeai")

    def stream_query(
        self,
        prompt: str,
        system_context: str,
        token_callback: Callable[[str], None],
        done_callback: Callable[[int, int], None],
        error_callback: Callable[[str], None],
    ) -> None:
        try:
            kwargs = {"model": self.model_id}
            if system_context:
                kwargs["system_instruction"] = system_context

            model = self._genai.GenerativeModel(**kwargs)
            response = model.generate_content(prompt, stream=True)

            for chunk in response:
                try:
                    if chunk.text:
                        token_callback(chunk.text)
                except Exception:
                    pass

            # Usage is available after iteration completes
            try:
                usage = response.usage_metadata
                in_tok = usage.prompt_token_count or 0
                out_tok = usage.candidates_token_count or 0
            except Exception:
                in_tok = 0
                out_tok = 0

            done_callback(in_tok, out_tok)

        except Exception as exc:
            error_callback(f"Google API error: {exc}")
