from __future__ import annotations

import json
import logging
import re
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
If the answer is supported by the context, include at least one citation like [1].
Answer in one brief sentence. Do not use bullet points, lists, or extra explanation.
Cite only the sources you actually use. Do not include unused sources.
If the context does not contain enough information, say so — do not invent facts.

Context:
{context}

Question: {question}

Return ONLY valid JSON with no explanation or markdown, in this exact format:
{{"answer": "your answer here with [1] citations"}}"""


def _normalize_json_like(text: str) -> str:
    # Remove trailing commas and normalize JSON-like output from the LLM.
    text = re.sub(r",\s*([}\]])", r"\1", text)
    return text.strip()


def _extract_answer_fallback(text: str) -> str | None:
    match = re.search(r'"answer"\s*:\s*"([^"]+)"', text)
    if match:
        return match.group(1)

    match = re.search(r"answer\s*[:=]\s*\"([^\"]+)\"", text)
    if match:
        return match.group(1)

    return None


def _extract_citation_numbers(answer: str) -> set[int]:
    return {int(num) for num in re.findall(r"\[(\d+)\]", answer)}


def _build_references(
    chunks: list[dict], cited_numbers: set[int] | None = None
) -> list[dict]:
    references = []
    for i, chunk in enumerate(chunks, 1):
        if cited_numbers is not None and i not in cited_numbers:
            logger.debug(
                "_build_references: skipping chunk %d (not in cited_numbers=%s)",
                i,
                cited_numbers,
            )
            continue
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


def _strip_citation_markers(answer: str) -> str:
    """Remove all [N] markers from the answer text."""
    return re.sub(r"\[\d+\]", "", answer).strip()


def _renumber_references(references: list[dict]) -> list[dict]:
    """Reassign reference numbers sequentially starting from 1."""
    return [{**ref, "number": i} for i, ref in enumerate(references, 1)]


def synthesize(question: str, chunks: list[dict]) -> dict:
    logger.debug("synthesize called: question=%r, chunks=%d", question, len(chunks))

    if not chunks:
        logger.warning("synthesize: no chunks provided, returning early")
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
    logger.debug("synthesize: prompt built (%.3f s)", prompt_time)

    llm_start = time.perf_counter()
    raw_response = llm.ask_llm(prompt)
    llm_time = time.perf_counter() - llm_start
    logger.debug("synthesize: raw LLM response (%.3f s):\n%s", llm_time, raw_response)

    # Strip markdown fences if the model adds them despite instructions
    cleaned = (
        raw_response.strip()
        .removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )
    logger.debug("synthesize: after fence stripping:\n%s", cleaned)

    # Normalize JSON-like output that may include trailing commas from the model.
    normalized = _normalize_json_like(cleaned)
    logger.debug("synthesize: after normalization:\n%s", normalized)

    parse_start = time.perf_counter()
    answer = raw_response  # fallback if everything fails
    try:
        parsed = json.loads(normalized)
        if isinstance(parsed, dict):
            answer = parsed.get("answer", raw_response)
            logger.debug("synthesize: JSON parse succeeded, answer=%r", answer)
        else:
            logger.warning(
                "synthesize: JSON parsed but not a dict (got %s), falling back",
                type(parsed),
            )
    except json.JSONDecodeError as exc:
        logger.warning("synthesize: JSON parse failed (%s), trying regex fallback", exc)
        extracted = _extract_answer_fallback(normalized)
        if extracted:
            answer = extracted
            logger.debug(
                "synthesize: regex fallback on normalized succeeded: %r", answer
            )
        else:
            extracted = _extract_answer_fallback(raw_response)
            if extracted:
                answer = extracted
                logger.debug(
                    "synthesize: regex fallback on raw_response succeeded: %r", answer
                )
            else:
                answer = raw_response
                logger.warning(
                    "synthesize: all extraction methods failed, using raw_response as answer"
                )

    citation_numbers = _extract_citation_numbers(answer)
    logger.debug(
        "synthesize: citation numbers extracted from answer: %s", citation_numbers
    )

    # BUG GUARD: if the LLM produced no citations at all, include all chunks
    # rather than returning an empty references list.
    if not citation_numbers:
        logger.warning(
            "synthesize: no citation markers found in answer=%r — "
            "LLM ignored the citation instruction. Including all %d chunks as references.",
            answer,
            len(chunks),
        )
        references = _build_references(chunks, cited_numbers=None)
    else:
        references = _build_references(chunks, cited_numbers=citation_numbers)
    answer = _strip_citation_markers(answer)
    references = _renumber_references(references)
    include_sources = bool(references)
    logger.debug(
        "synthesize: references built: %d items, include_sources=%s",
        len(references),
        include_sources,
    )

    parse_time = time.perf_counter() - parse_start
    total_time = time.perf_counter() - total_start

    logger.info(
        "synthesize completed in %.3f s (prompt=%.3f, llm=%.3f, parse=%.3f, chunks=%d, refs=%d)",
        total_time,
        prompt_time,
        llm_time,
        parse_time,
        len(chunks),
        len(references),
    )

    return {
        "disclaimer": DISCLAIMER,
        "answer": answer,
        "references": references,
        "include_sources": include_sources,
    }


if __name__ == "__main__":
    # Enable debug logging so all the new log lines are visible when running directly
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s %(name)s: %(message)s",
    )

    from rag.retrieve import retrieve
    from rag.rewrite import rewrite_query

    question = "does sugar cause diabetes?"
    print(f"User question: {question}\n")

    start = time.perf_counter()
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
