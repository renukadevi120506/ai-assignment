import json
import os
import re
from typing import Any

import requests
from pydantic import BaseModel

from app.ai.llm_provider import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = (base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.model = model or os.environ.get("OLLAMA_MODEL", "llama3")

    def _clean_json_text(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
        return text.strip()

    def generate_text(self, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3}
        }
        res = requests.post(url, json=payload, timeout=90)
        res.raise_for_status()
        return res.json().get("response", "")

    def generate_json(self, prompt: str, schema_class: type[BaseModel]) -> dict[str, Any]:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": f"{prompt}\nReturn strict JSON matching the schema.",
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.2}
        }
        res = requests.post(url, json=payload, timeout=90)
        res.raise_for_status()
        raw_text = res.json().get("response", "{}")
        cleaned = self._clean_json_text(raw_text)
        
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as e:
            match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
            if match:
                parsed = json.loads(match.group(1))
            else:
                raise ValueError(f"Failed to parse Ollama JSON output: {e}. Output was: {raw_text[:200]}")
                
        validated = schema_class.model_validate(parsed)
        return validated.model_dump()
