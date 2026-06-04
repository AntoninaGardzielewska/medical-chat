import os

import httpx

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


class OllamaChat:
    def __init__(self, model: str = "llama3.2:latest"):
        self.client = httpx.Client(timeout=120.0)
        self.model = model

    def ask_llm(self, prompt: str) -> str:
        try:
            response = self.client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
        except (httpx.RequestError, httpx.HTTPStatusError, httpx.ReadTimeout) as e:
            raise RuntimeError(
                f"Ollama is unreachable or returned an error: {e}"
            ) from e

        return response.json()["response"]

    def rewrite_user_query(self, user_question: str) -> str:
        prompt = f"""
            You are a medical research asistent.
            Rewrite the following question into precise clinical language suitable for searching PubMed literature.
            Return only the rewritten query, nothing else.
            Question: {user_question}
        """
        return self.ask_llm(prompt)
