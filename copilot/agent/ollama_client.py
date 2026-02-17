import logging
from typing import Dict
import requests
import time

LOGGER = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout_seconds: int = 45):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    # --------------------------------------------------
    # Health Check
    # --------------------------------------------------
    def health_check(self) -> bool:
        try:
            resp = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5,
            )
            if resp.status_code != 200:
                return False

            tags = resp.json().get("models", [])
            return any(self.model in m.get("name", "") for m in tags)

        except Exception as exc:
            LOGGER.warning("Ollama health check failed: %s", exc)
            return False

    # --------------------------------------------------
    # Generate (DEMO OPTIMIZED)
    # --------------------------------------------------
    def generate(self, prompt: str) -> str:
        """
        Fast, demo-safe generation.
        Forces short answers and prevents long reasoning delays.
        """

        # 🔥 Force concise response to reduce token explosion
        demo_prompt = (
            "Answer concisely in under 5 bullet points.\n\n"
            f"{prompt}"
        )

        payload: Dict = {
            "model": self.model,
            "prompt": demo_prompt,
            "stream": False,
            "options": {
                # 🚀 PERFORMANCE OPTIMIZED
                "temperature": 0.2,
                "num_predict": 80,        # HARD LIMIT (very important)
                "top_k": 20,
                "top_p": 0.8,
                "repeat_penalty": 1.05,
                "num_ctx": 1024,          # prevent memory overload
            },
        }

        for attempt in range(2):  # 🔁 Simple retry
            try:
                resp = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout_seconds,
                )
                resp.raise_for_status()

                body = resp.json()
                response = body.get("response", "").strip()

                if not response:
                    return "⚠️ AI returned an empty response."

                return response

            except requests.exceptions.Timeout:
                LOGGER.error("Ollama request timed out (attempt %s)", attempt + 1)
                if attempt == 0:
                    time.sleep(2)
                    continue
                return "⚠️ AI response timed out. Please ask a shorter question."

            except requests.exceptions.ConnectionError:
                LOGGER.error("Ollama connection error")
                return "⚠️ Unable to connect to AI model service."

            except Exception as e:
                LOGGER.error("Ollama generation failed: %s", e)
                return "⚠️ AI encountered an unexpected error."

        return "⚠️ AI failed after retry."
