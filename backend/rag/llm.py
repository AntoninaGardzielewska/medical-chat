import httpx

from src.config import settings


class OllamaChat:
    def __init__(self, model: str = "llama3.2:latest"):
        self.client = httpx.Client(timeout=120.0)
        self.model = model
        self.base_url = settings.ollama_base_url

    def ask_llm(self, prompt: str) -> str:
        try:
            response = self.client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
        except (httpx.RequestError, httpx.HTTPStatusError, httpx.ReadTimeout) as e:
            raise RuntimeError(
                f"Ollama is unreachable or returned an error: {e}"
            ) from e

        return response.json()["response"]
