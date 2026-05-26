# Corpus Scope

> Documents the topic areas chosen for the MVP corpus, the rationale behind each decision, and the ingestion parameters used.

---

## Chosen MeSH Topic Areas

| Topic | MeSH Term | Rationale |
|---|---|---|
| Type 2 Diabetes | `type 2 diabetes` | High global burden, extensively researched, rich abstract literature |
| Hypertension | `hypertension` | Most common cardiovascular condition, large volume of review literature |
| Heart Failure | `heart failure` | Frequently comorbid with both above topics, strong clinical relevance |

These three topics were chosen because:
- They are among the most studied conditions in internal medicine
- They frequently co-occur in patients, making cross-topic retrieval meaningful
- They have a large volume of high-quality review articles on PubMed

---

## Article Type Filter

We filter for **Review** and **Systematic Review** articles only.

**Why?**
- Review articles synthesise findings across many studies — they are inherently high-quality and widely cited
- Systematic reviews follow strict methodology and represent the strongest evidence tier
- This acts as a proxy for citation quality without needing external citation count APIs
- Keeps the corpus focused and avoids low-quality or retracted individual studies

---

## Ingestion Parameters

| Parameter | Value | Reason |
|---|---|---|
| Articles per topic | 1000 | |
| Sort order | `relevance` | PubMed's default quality signal |
| Batch size | 200 | PubMed `efetch` API limit per request |
| Rate limit | 3 requests/sec | PubMed E-utilities policy |
| Fields stored | pmid, title, abstract, authors, journal, year | Minimum needed for RAG + citation display |

---
