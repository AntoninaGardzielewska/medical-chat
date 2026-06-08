from __future__ import annotations

import json

from rag.llm import OllamaChat

DISCLAIMER = (
    "⚠️ This information is for research and educational purposes only. "
    "It is not a substitute for professional medical advice, diagnosis, or treatment. "
    "Always consult a qualified healthcare provider."
)

_llm = OllamaChat()


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
        references.append({
            "number": i,
            "pmid": pmid,
            "title": chunk.get("title", ""),
            "authors": _format_authors(chunk.get("authors", [])),
            "journal": chunk.get("journal", ""),
            "year": chunk.get("year", ""),
            "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        })
    return references


def synthesize(question: str, chunks: list[dict]) -> dict:
    if not chunks:
        return {
            "disclaimer": DISCLAIMER,
            "answer": "No relevant articles were found for your question.",
            "references": [],
        }

    prompt = _build_prompt(question, chunks)
    raw_response = _llm.ask_llm(prompt)

    # Strip markdown fences if the model adds them despite instructions
    cleaned = raw_response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        parsed = json.loads(cleaned)
        answer = parsed.get("answer", raw_response)
    except json.JSONDecodeError:
        # Use raw text if JSON parsing fails
        answer = raw_response

    return {
        "disclaimer": DISCLAIMER,
        "answer": answer,
        "references": _build_references(chunks),
    }

if __name__ == "__main__":
    import time
    from rag.rewrite import rewrite_query
    from rag.retrieve import retrieve

    question = "does sugar cause diabetes?"
    print(f"User question: {question}\n")

    start = time.time()
    rewritten = rewrite_query(question)
    print(f"Rewritten query: {rewritten}\n")

    chunks = retrieve(rewritten, k=2)
    print(f"Retrieved {len(chunks)} chunks\n")

    result = synthesize(question, chunks)
    print("=" * 60)
    print(result["disclaimer"])
    print("=" * 60)
    print(result["answer"])
    print("\nREFERENCES:")
    for ref in result["references"]:
        print(f"[{ref['number']}] {ref['authors']} ({ref['year']}). {ref['title']}. {ref['journal']}.")
        print(f"    {ref['pubmed_url']}")