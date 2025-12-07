# Contract Intelligence API (FastAPI)

## What this repo provides
A production-ish FastAPI service that:
- ingests PDF contracts
- extracts structured fields (parties, effective_date, term, governing_law, etc.)
- runs RAG (retrieve + generate) Q&A over uploaded docs with citations
- runs rule-based clause-risk audits
- streams answers over WebSocket
- optionally posts webhooks when long tasks complete
- admin endpoints: /healthz, /metrics, /docs

## Quickstart (local)
1. Create a python env (or use Docker).
2. Install: `pip install -r requirements.txt`
3. Run: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
4. Open Swagger: http://localhost:8000/docs

## Using Docker


cd docker
docker-compose up --build


## Environment variables
- `EMBED_MODEL` (defaults to `sentence-transformers/all-MiniLM-L6-v2`)
- `OPENAI_API_KEY` (optional — improves extraction & final answer quality)

## File upload example (curl)


curl -X POST "http://localhost:8000/api/ingest
"
-F "files=@/path/to/contract1.pdf"
-F "files=@/path/to/contract2.pdf"


## Ask example


curl -X POST "http://localhost:8000/api/ask
" -H "Content-Type: application/json"
-d '{"question":"What is the governing law?","document_ids":null}'


## WebSocket stream example (JS)
```js
const ws = new WebSocket("ws://localhost:8000/api/ask/stream");
ws.onopen = () => ws.send(JSON.stringify({question:"When does this auto-renew?", top_k:4}));
ws.onmessage = (ev) => console.log("msg", JSON.parse(ev.data));

Sample public PDFs (put links here)

Example NDA: https://www.sec.gov/Archives/edgar/data/320193/000119312520043588/d912954dex102.htm

Example GPL (license): https://www.gnu.org/licenses/gpl-3.0.pdf

Public ToS (example): https://www.apple.com/legal/internet-services/itunes/us/terms.html

What to submit

This repository contains code, prompts, eval/ and a short DESIGN.md for architecture notes.

Notes & trade-offs

Extraction currently uses regex heuristics + optional OpenAI prompt.

Retrieval uses sentence-transformers + FAISS; embeddings persisted to data/vecs.* files.

SQLite is used for metadata for simplicity; production should use Postgres + managed vector DB.


---

## `DESIGN.md`
```markdown
# Design (<= 2 pages) — Contract Intelligence API

## Architecture
- FastAPI app with modular routers (`app/api/*`).
- Data store:
  - SQLite (SQLAlchemy) for documents and chunk metadata.
  - Filesystem `data/uploads` for PDFs and `data/texts` for full text.
  - FAISS index files stored under `data/faiss.*` with a sidecar JSON for metadata.
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2` by default (lightweight).
- LLM: optional OpenAI (fallback to extractive heuristics if not provided).

## Chunking rationale
- Chunking by page with additional overlap option; default page-sized chunks preserve clause boundaries and make evidence attribution simple (document_id + page).
- If a page is huge, chunk into ~800-character windows with 200-character overlap.

## Data model
- Document (id, filename, uploaded_at, num_pages, path_pdf, path_text)
- Chunk (id, document_id, page_no, char_start, char_end, text)

## RAG Flow
1. Embed query.
2. Retrieve top-K page chunks from FAISS.
3. Create a RAG prompt containing retrieved contexts + metadata.
4. Call LLM (OpenAI) if available; otherwise run extractive fallback (score overlap sentences).

## Audit
- Rule-based regex patterns for auto-renewal, unlimited liability, indemnity, missing confidentiality.
- Returns severity + evidence (document_id, page_no, char ranges, snippet).

## Fallbacks
- If OpenAI not available: use extractive heuristic (token overlap) to produce answers; still supply citations.
- If FAISS missing: return text search fallback (SQLite LIKE queries).

## Security & Prod Notes
- Add authentication (API keys / OAuth), rate-limiting, request size limits.
- Move PDF blob storage to S3, vector DB to Milvus/Pinecone/Weaviate for scale.
- Sanitize extracted text, avoid storing PII in plain sight when not required.

### Components
- FastAPI Gateway
- RAG Engine (retriever + LLM)
- Vector Store (FAISS CPU)
- Document Parser (PyMuPDF)
- LLM Layer (OpenAI GPT)

## 2. Data Model

### Document Table
- id (UUID)
- file_name
- source_type
- uploaded_at

### Chunk Table
- chunk_id
- document_id
- chunk_text
- page_num
- embedding
- token_len

## 3. Chunking Rationale
- 350–450 character chunks
- 50–70 character overlap
- Sliding window algorithm

## 4. Retrieval Strategy
- Top-k FAISS search (k=6)
- Optional re-ranking

## 5. Answer Generation Logic
Prompt template ensures grounded answers.

## 6. Fallback Behaviors
- No chunks → “No relevant content found.”
- Missing docs → Upload required.

## 7. Security Considerations
- File scanning
- PII masking
- Auth + rate limiting
- Prevent prompt injection

## 8. Observability
- Log performance, not document content
"""

output_path = "/mnt/data/rag_design_doc.md"
convert_text(md_content, 'md', format='md', outputfile=output_path, extra_args=['--standalone'])

output_path
