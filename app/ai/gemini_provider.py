import json
import os
import re
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.ai.llm_provider import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
        self._client = None

    def _get_client(self):
        if not self._client:
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY is not set. Please provide a valid Gemini API key.")
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _clean_json_text(self, text: str) -> str:
        """Strip markdown code block tags and surrounding whitespace."""
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
        return text.strip()

    def generate_text(self, prompt: str) -> str:
        client = self._get_client()
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.3)
        )
        return response.text or ""

    def generate_json(self, prompt: str, schema_class: type[BaseModel]) -> dict[str, Any]:
        client = self._get_client()
        
        # Configure JSON response mime type
        config = types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json"
        )
        
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config
        )
        
        raw_text = response.text or "{}"
        cleaned = self._clean_json_text(raw_text)
        
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as e:
            # Fallback regex extraction of JSON object or array
            match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
            if match:
                parsed = json.loads(match.group(1))
            else:
                raise ValueError(f"Failed to parse LLM JSON response: {e}. Output was: {raw_text[:200]}")

        # Validate with Pydantic
        validated = schema_class.model_validate(parsed)
        return validated.model_dump()
