import logging
from typing import Dict
import requests


LOGGER = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout_seconds: int = 120):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def health_check(self) -> bool:
        try:
            resp = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10,
            )
            if resp.status_code != 200:
                return False
            tags = resp.json().get("models", [])
            return any(self.model in m.get("name", "") for m in tags)
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

        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout_seconds,
            )
            resp.raise_for_status()
            body = resp.json()
            return body.get("response", "")
        except requests.exceptions.Timeout:
            LOGGER.error("Ollama request timed out")
            return "⚠️ AI model took too long to respond. Please try again."
        except Exception as e:
            LOGGER.error("Ollama generation failed: %s", e)
            return "⚠️ Unable to get response from AI model."
