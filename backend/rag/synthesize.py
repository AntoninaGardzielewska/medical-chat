from __future__ import annotations

import json
import logging
import time

from rag.llm import OllamaChat

logger = logging.getLogger(__name__)

DISCLAIMER = (
    "⚠️ This information is for research and educational purposes only. "
    "It is not a substitute for professional medical advice, diagnosis, or treatment. "
    "Always consult a qualified healthcare provider."
)

_llm = None


def _get_llm():
    """Lazy initialization of OllamaChat."""
    global _llm
    if _llm is None:
        _llm = OllamaChat()
    return _llm


def _format_authors(authors_raw: str | list) -> str:
    """Convert authors JSON string → 'Smith J, Jones A' display format."""
    if isinstance(authors_raw, str):
        try:
            authors = json.loads(authors_raw)
        except json.JSONDecodeError:
            return authors_raw
    else:
        authors = authors_raw

    parts = []
    for author in authors[:3]:  # cap at 3 authors, then "et al."
        last = author.get("last_name", "")
        first = author.get("first_name", "")
        initials = first[0] if first else ""
        if last:
            parts.append(f"{last} {initials}".strip())

    result = ", ".join(parts)
    if len(authors) > 3:
        result += " et al."
    return result or "Unknown"


def _build_prompt(question: str, chunks: list[dict]) -> str:
    context_blocks = []
    for i, chunk in enumerate(chunks, 1):
        authors_display = _format_authors(chunk.get("authors", []))
        block = (
            f"[{i}] PMID: {chunk.get('pmid', 'N/A')} | "
            f"Title: {chunk.get('title', 'N/A')} | "
            f"Authors: {authors_display} | "
            f"Year: {chunk.get('year', 'N/A')}\n"
            f"Text: {chunk.get('text', '')}"
        )
        context_blocks.append(block)

    context = "\n\n".join(context_blocks)

    return f"""You are a medical research assistant. Answer the question using ONLY the context provided below.
Use inline citations like [1], [2] referring to the numbered sources.
If the context does not contain enough information, say so — do not invent facts.

Context:
{context}

Question: {question}

Return ONLY valid JSON with no explanation or markdown, in this exact format:
{{"answer": "your answer here with [1] citations"}}"""


def _build_references(chunks: list[dict]) -> list[dict]:
    references = []
    for i, chunk in enumerate(chunks, 1):
        pmid = chunk.get("pmid", "")
        references.append(
            {
                "number": i,
                "pmid": pmid,
                "title": chunk.get("title", ""),
                "authors": _format_authors(chunk.get("authors", [])),
                "journal": chunk.get("journal", ""),
                "year": chunk.get("year", ""),
                "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            }
        )
    return references


def synthesize(question: str, chunks: list[dict]) -> dict:
    if not chunks:
        return {
            "disclaimer": DISCLAIMER,
            "answer": "I could not find enough evidence to answer your question.",
            "references": [],
            "include_sources": False,
        }

    total_start = time.perf_counter()
    llm = _get_llm()

    prompt_start = time.perf_counter()
    prompt = _build_prompt(question, chunks)
    prompt_time = time.perf_counter() - prompt_start

    llm_start = time.perf_counter()
    raw_response = llm.ask_llm(prompt)
    llm_time = time.perf_counter() - llm_start

    # Strip markdown fences if the model adds them despite instructions
    cleaned = (
        raw_response.strip()
        .removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )

    parse_start = time.perf_counter()
    try:
        parsed = json.loads(cleaned)
        answer = parsed.get("answer", raw_response)
    except json.JSONDecodeError:
        answer = raw_response
    parse_time = time.perf_counter() - parse_start
    total_time = time.perf_counter() - total_start

    logger.info(
        "synthesize completed in %.3f s (prompt=%.3f, llm=%.3f, parse=%.3f, chunks=%d)",
        total_time,
        prompt_time,
        llm_time,
        parse_time,
        len(chunks),
    )

    return {
        "disclaimer": DISCLAIMER,
        "answer": answer,
        "references": _build_references(chunks),
        "include_sources": bool(chunks),
    }


if __name__ == "__main__":
    import time

    from rag.retrieve import retrieve
    from rag.rewrite import rewrite_query

    question = "does sugar cause diabetes?"
    print(f"User question: {question}\n")

    start = time.time()
    rewritten = rewrite_query(question)
    print(f"Rewritten query: {rewritten}\n")

    chunks = retrieve(rewritten, max_results=2)
    print(f"Retrieved {len(chunks)} chunks\n")

    result = synthesize(question, chunks)
    print("=" * 60)
    print(result["disclaimer"])
    print("=" * 60)
    print(result["answer"])
    print("\nREFERENCES:")
    for ref in result["references"]:
        print(
            f"[{ref['number']}] {ref['authors']} ({ref['year']}). {ref['title']}. {ref['journal']}."
        )
        print(f"    {ref['pubmed_url']}")
