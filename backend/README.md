# ConceptGraph AI — Backend

FastAPI backend: PDF → Gemini concept extraction → prerequisite knowledge graph → diagnostic quiz →
deterministic knowledge-gap analysis and prerequisite-ordered learning path.

- **API contract:** [../API_CONTRACT.md](../API_CONTRACT.md)
- **Swagger UI:** http://localhost:8000/docs
- **OpenAPI spec:** http://localhost:8000/openapi.json (copy committed at [openapi.json](openapi.json))

## Run locally

Requires Python 3.11+ (developed on 3.13.1).

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env        # then set GEMINI_API_KEY
python -m uvicorn app.main:app --reload --port 8000   # run with the venv active
```

### Mock mode (frontend developers — no API key needed)

```bash
# macOS/Linux
AI_MODE=mock python -m uvicorn app.main:app --reload --port 8000
# Windows PowerShell
$env:AI_MODE="mock"; python -m uvicorn app.main:app --reload --port 8000
```

Any text PDF (e.g. [samples/sample_lecture.pdf](samples/sample_lecture.pdf)) returns a fixed 9-concept
graph and 12-question quiz. The answer key is in API_CONTRACT.md.

### Quick check with curl

```bash
curl localhost:8000/health
curl -F "file=@samples/sample_lecture.pdf" localhost:8000/api/analyze
curl localhost:8000/api/quiz/<session_id>
curl -X POST localhost:8000/api/quiz/<session_id>/submit \
     -H "Content-Type: application/json" \
     -d '{"answers":[{"question_id":"q1","selected_option_id":"B"}]}'
curl localhost:8000/api/results/<session_id>
```

### Generate TypeScript types (frontend)

```bash
npx openapi-typescript http://localhost:8000/openapi.json -o src/api/schema.d.ts
```

After changing models, regenerate the committed spec: `python scripts/export_openapi.py`.

## Tests

```bash
cd backend
pytest -q
```

Tests never call the real Gemini API (AI is mocked/faked throughout).

## Architecture

```
app/
  main.py                 App factory, CORS, wiring
  config.py               Env-based settings
  models.py               Pydantic API schemas (the contract)
  errors.py               Error types + {"error": {...}} envelope
  rate_limit.py           Per-IP sliding-window throttling
  api/routes.py           Endpoints
  services/
    pdf_service.py        Validation, extraction, token estimate, chunking
    gemini_client.py      Gemini transport: timeout, retries, concurrency cap, model failover
    ai_service.py         Prompts, concept extraction (direct/chunked), quiz generation, output validation
    mock_ai.py            Canned AI responses for AI_MODE=mock
    graph_service.py      Validation, cycle detection, repair, descendants, topological sort, serialization
    quiz_service.py       Quiz concept selection, answer-free payloads, grading
    gap_service.py        Mastery, priority = (1 - score) * (1 + 0.25 * descendants), explanations
    learning_path_service.py  Prerequisite-respecting, priority-tie-broken study order
    session_service.py    In-memory sessions with TTL and per-session locks
```

### Key behaviours

- **Token budgeting:** ≤ 15k estimated tokens → one Gemini call. Larger → paragraph-aware ~4k-token chunks
  (max 10, 2 concurrent) extracted independently, then one consolidation call merges them. Documents over
  `MAX_DOCUMENT_TOKENS` or needing more than `MAX_CHUNKS` are rejected with `413 document_too_long`; sections
  are never silently dropped.
- **AI output is untrusted:** document text is fenced as data in prompts; responses are schema-validated,
  IDs normalized, duplicates merged, unknown/self references removed, cycles broken (reported in
  `processing_status.warnings`). Invalid output is retried, then `502 ai_invalid_response`.
- **Model failover:** if `GEMINI_MODEL` times out, is overloaded (5xx) or rate limited (429), the request
  goes straight to `GEMINI_FALLBACK_MODEL` (default `gemini-2.5-flash-lite`), which gets up to 2 retries.
- **Quiz:** generated on the first `GET /api/quiz/{id}` for the 6 concepts with the most dependents, 2
  questions each. Options are shuffled server-side; answer keys never leave the backend before submission.
  The document excerpt used for grounding is discarded once the quiz exists. The original PDF is never stored.
- **Grading:** one submission per session (`409 already_submitted` after). Unanswered = incorrect.
  Unassessed concepts get `score: null`, never 0.

## Environment variables

See [.env.example](.env.example) for the full list with defaults. The important ones:

| Variable | Default | Notes |
|---|---|---|
| `GEMINI_API_KEY` | — | Required unless `AI_MODE=mock`. Backend only. |
| `AI_MODE` | `gemini` | `mock` for canned responses. |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Switched from 3.8 Flash on 2026-10-10 (3.8 was timing out). |
| `GEMINI_FALLBACK_MODEL` | `gemini-2.5-flash-lite` | Empty string disables failover. |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated. Add the deployed frontend URL. |
| `SESSION_TTL_MINUTES` | `120` | |

## Deploy to Render

[`../render.yaml`](../render.yaml) defines the service (root dir `backend`, one worker, health check `/health`,
`PYTHON_VERSION=3.13.1`). In the Render dashboard: **New → Blueprint**, select the repo, then set
`GEMINI_API_KEY` and `CORS_ORIGINS` (e.g. `https://your-frontend.vercel.app`).

Manual setup equivalent:
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1`

## Limitations (MVP)

- **Sessions live in memory** and are lost on restart or redeploy (Render's free tier also sleeps when idle).
  Run exactly **one** worker process.
- Rate limiting is per process and per client IP.
- Token counts are estimates (≈ 4 characters per token), not exact Gemini counts.
- Scanned/image-only PDFs are rejected (no OCR).
