import logging
from typing import Dict

import requests


LOGGER = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout_seconds: int = 45):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def health_check(self) -> bool:
        try:
            resp = requests.get(
                f"{self.base_url}/api/tags", timeout=self.timeout_seconds
            )
            if resp.status_code != 200:
                return False
            tags = resp.json().get("models", [])
            return any(m.get("name", "").startswith(self.model) for m in tags)
        except Exception as exc:
            LOGGER.warning("Ollama health check failed: %s", exc)
            return False

    def generate(self, prompt: str) -> str:
        payload: Dict = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
            },
        }
        resp = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=self.timeout_seconds,
        )
        resp.raise_for_status()
        body = resp.json()
        return body.get("response", "")
