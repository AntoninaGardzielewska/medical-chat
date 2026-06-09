import logging
import time

from rag.llm import OllamaChat

logger = logging.getLogger(__name__)
_llm = OllamaChat()


def rewrite_query(user_question: str) -> str:
    start = time.perf_counter()
    prompt = f"""
        You are a medical research asystent.
        Rewrite the following question into precise clinical language suitable for searching PubMed literature.
        Return only the rewritten query, nothing else.
        Question: {user_question}
    """
    answer = _llm.ask_llm(prompt)
    duration = time.perf_counter() - start
    logger.info(
        "rewrite_query completed in %.3f s (question length=%d, rewritten length=%d)",
        duration,
        len(user_question),
        len(answer.strip()),
    )
    return answer.strip().strip('"')


if __name__ == "__main__":
    questions = [
        "does sugar cause diabetes?",
        "metformin efficacy T2DM",
        "what helps with high blood pressure?",
    ]
    for question in questions:
        start = time.time()
        print(
            f"original question: {question}\n rewritten question: {rewrite_query(question)}"
        )
        end = time.time()
        print(f"time: {end - start} \n\n\n")
