import logging
import time

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


class OllamaChat:
    def __init__(self, model: str = "llama3.2:latest"):
        self.client = httpx.Client(timeout=120.0)
        self.model = model
        self.base_url = settings.ollama_base_url

    def ask_llm(self, prompt: str) -> str:
        start = time.perf_counter()
        try:
            response = self.client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
        except (httpx.RequestError, httpx.HTTPStatusError, httpx.ReadTimeout) as e:
            duration = time.perf_counter() - start
            logger.error(
                "Ollama ask_llm failed after %.3f s: %s",
                duration,
                str(e),
            )
            raise RuntimeError(
                f"Ollama is unreachable or returned an error: {e}"
            ) from e
        duration = time.perf_counter() - start
        logger.info("Ollama ask_llm completed in %.3f s", duration)
        return response.json()["response"]
