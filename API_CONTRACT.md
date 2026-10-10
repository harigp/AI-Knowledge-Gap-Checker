# ConceptGraph AI — Backend API Contract

**Version:** 1.0.0  **Status:** Stable for frontend integration
**Base URL (local):** `http://localhost:8000`  **Swagger UI:** `/docs`  **OpenAPI JSON:** `/openapi.json` (a copy is committed at `backend/openapi.json`)

> Breaking changes to anything in this document will be announced to the frontend team first and recorded in the [Changelog](#changelog).

## Conventions

- All JSON fields use **snake_case**.
- All timestamps are ISO-8601 UTC strings, e.g. `"2026-10-10T14:05:12.345Z"`.
- Concept IDs are stable snake_case strings (e.g. `"simple_linear_regression"`) and are safe to use as React Flow node IDs.
- Scores are floats in `[0, 1]`, rounded to 4 decimals. Priorities are rounded to 4 decimals.
- Every error response uses the same envelope (see [Errors](#errors)).
- Sessions live **in memory** for `SESSION_TTL_MINUTES` (default 120). They are lost when the backend restarts. On `404 session_not_found`, send the user back to the upload screen.

## Typical flow

```
POST /api/analyze (PDF)         → session_id + concept graph
GET  /api/graph/{session_id}    → same graph (for reloads)
GET  /api/quiz/{session_id}     → questions (no answers); first call generates the quiz (~5–20 s)
POST /api/quiz/{session_id}/submit → scores, gaps, recommendations, learning path
GET  /api/results/{session_id}  → same results again (for reloads)
```

## Mock mode for frontend development

Run the backend with `AI_MODE=mock` (see `backend/README.md`). No Gemini key is required; any valid text PDF returns a fixed 9-concept statistics graph and a fixed 12-question quiz. All examples below come from mock mode. The correct answer for every mock question is listed in [Mock answer key](#mock-answer-key) so you can test the "strong" and "weak" paths.

---

## Endpoints

### `GET /health`

Liveness check. Exposes no secrets.

**200**
```json
{
  "status": "ok",
  "service": "conceptgraph-backend",
  "version": "1.0.0",
  "ai_configured": true,
  "timestamp": "2026-10-10T14:05:12.345Z"
}
```

---

### `POST /api/analyze`

Upload lecture notes and build the concept graph.

**Request:** `multipart/form-data` with one field:

| Field | Type | Required | Notes |
|---|---|---|---|
| `file` | file | yes | `.pdf`, ≤ 10 MB, ≤ 50 pages, must contain selectable text |

```js
const form = new FormData();
form.append("file", file);
const res = await fetch(`${API}/api/analyze`, { method: "POST", body: form });
```

**Expected duration:** typically 5–30 s; up to ~60 s when the primary Gemini model is slow and the backend fails over to the fallback model. Show a loading state and use a client timeout of at least 120 s.

**200 — `AnalyzeResponse`**
```json
{
  "session_id": "Xk2v9w7bQ4mJr1tLzP8sYc3nHf6dAe0u",
  "document_name": "lecture7_regression.pdf",
  "concepts": [
    {
      "id": "probability_basics",
      "name": "Probability Basics",
      "description": "Sample spaces, events, and the rules for computing probabilities.",
      "difficulty": "beginner",
      "prerequisites": [],
      "source_type": "inferred",
      "descendant_count": 3,
      "level": 0
    },
    {
      "id": "random_variables",
      "name": "Random Variables",
      "description": "Numeric outcomes of random processes, their distributions, expectation and variance.",
      "difficulty": "intermediate",
      "prerequisites": ["probability_basics"],
      "source_type": "document",
      "descendant_count": 2,
      "level": 1
    }
  ],
  "edges": [
    {
      "id": "probability_basics->random_variables",
      "source": "probability_basics",
      "target": "random_variables",
      "relationship": "prerequisite"
    }
  ],
  "topological_order": ["algebra_fundamentals", "probability_basics", "descriptive_statistics", "random_variables", "correlation", "hypothesis_testing", "simple_linear_regression", "least_squares_estimation", "regression_inference"],
  "processing_status": {
    "status": "completed",
    "processing_mode": "direct",
    "page_count": 6,
    "estimated_tokens": 3120,
    "chunk_count": 1,
    "concept_count": 9,
    "ai_requests_used": 1,
    "quiz_status": "pending",
    "warnings": []
  },
  "expires_at": "2026-10-10T16:05:12.345Z"
}
```

(The `concepts`/`edges` arrays above are truncated; a real response has all concepts and edges.)

**Errors:** `400 invalid_file_type`, `400 invalid_pdf`, `400 empty_pdf`, `400 encrypted_pdf`, `400 no_extractable_text`, `400 too_many_pages`, `413 file_too_large`, `413 document_too_long`, `422 validation_error` (missing `file` field), `429 rate_limited`, `502 ai_invalid_response`, `503 ai_unavailable`, `503 ai_budget_exceeded`, `503 ai_not_configured`.

---

### `GET /api/graph/{session_id}`

**200 — `GraphResponse`**
```json
{
  "session_id": "Xk2v9w7bQ4mJr1tLzP8sYc3nHf6dAe0u",
  "document_name": "lecture7_regression.pdf",
  "concepts": [ /* Concept[] — same as /api/analyze */ ],
  "edges": [ /* Edge[] */ ],
  "topological_order": [ /* string[] */ ]
}
```

**Errors:** `404 session_not_found`.

---

### `GET /api/quiz/{session_id}`

Returns the diagnostic quiz. The **first** call generates it with Gemini (typically 5–20 s, up to ~60 s on failover); later calls return the cached quiz instantly. Concurrent first calls are safe (only one generation runs).

Answers and explanations are **never** included here.

**200 — `QuizResponse`**
```json
{
  "session_id": "Xk2v9w7bQ4mJr1tLzP8sYc3nHf6dAe0u",
  "total_questions": 12,
  "assessed_concept_ids": ["algebra_fundamentals", "probability_basics", "descriptive_statistics", "random_variables", "correlation", "simple_linear_regression"],
  "submitted": false,
  "questions": [
    {
      "id": "q1",
      "concept_id": "algebra_fundamentals",
      "concept_name": "Algebra Fundamentals",
      "question": "What is the slope of the line y = 3x + 2?",
      "options": [
        { "id": "A", "text": "2" },
        { "id": "B", "text": "3" },
        { "id": "C", "text": "5" },
        { "id": "D", "text": "3/2" }
      ]
    }
  ]
}
```

**Errors:** `404 session_not_found`, `429 rate_limited`, `502 ai_invalid_response`, `503 ai_unavailable`, `503 ai_budget_exceeded`.

If generation fails, the call can simply be retried; the session stays valid.

---

### `POST /api/quiz/{session_id}/submit`

Grade answers and run gap analysis. Each session can be graded **once**.

**Request — `QuizSubmitRequest`** (`application/json`)
```json
{
  "answers": [
    { "question_id": "q1", "selected_option_id": "B" },
    { "question_id": "q2", "selected_option_id": "D" }
  ]
}
```

- Questions not included are graded as **unanswered** (counted incorrect; `selected_option_id: null` in results).
- An unknown `question_id`, or the same `question_id` twice, returns `400`.

**200 — `AssessmentResults`**
```json
{
  "session_id": "Xk2v9w7bQ4mJr1tLzP8sYc3nHf6dAe0u",
  "submitted_at": "2026-10-10T14:12:40.120Z",
  "overall_score": 0.5833,
  "total_correct": 7,
  "total_questions": 12,
  "unanswered_count": 0,
  "concept_scores": [
    { "concept_id": "algebra_fundamentals", "concept_name": "Algebra Fundamentals", "correct": 2, "total": 2, "score": 1.0, "mastery": "strong" },
    { "concept_id": "probability_basics", "concept_name": "Probability Basics", "correct": 0, "total": 2, "score": 0.0, "mastery": "weak" },
    { "concept_id": "correlation", "concept_name": "Correlation", "correct": 1, "total": 2, "score": 0.5, "mastery": "developing" },
    { "concept_id": "hypothesis_testing", "concept_name": "Hypothesis Testing", "correct": 0, "total": 0, "score": null, "mastery": "unassessed" }
  ],
  "question_results": [
    {
      "question_id": "q3",
      "concept_id": "probability_basics",
      "question": "A fair die is rolled once. What is the probability of rolling an even number?",
      "selected_option_id": "A",
      "correct_option_id": "C",
      "is_correct": false,
      "explanation": "Three of the six equally likely outcomes (2, 4, 6) are even, so P = 3/6 = 1/2."
    }
  ],
  "learning_gaps": [
    {
      "concept_id": "probability_basics",
      "concept_name": "Probability Basics",
      "score": 0.0,
      "mastery": "weak",
      "descendant_count": 3,
      "downstream_concept_ids": ["random_variables", "hypothesis_testing", "regression_inference"],
      "priority": 1.75,
      "reason": "You answered 0 of 2 questions on Probability Basics correctly (0%), so it is classified as weak. 3 other concepts in this lecture build on it (Random Variables, Hypothesis Testing, Regression Inference), giving it a review priority of 1.75."
    }
  ],
  "recommendations": [
    {
      "rank": 1,
      "concept_id": "probability_basics",
      "concept_name": "Probability Basics",
      "action": "review",
      "score": 0.0,
      "mastery": "weak",
      "descendant_count": 3,
      "priority": 1.75,
      "reason": "..."
    }
  ],
  "learning_path": {
    "total_steps": 4,
    "summary": "Study 4 concepts in this order. Each step comes after the prerequisites it depends on; when several concepts are ready at once, the one with the higher review priority comes first.",
    "steps": [
      {
        "step": 1,
        "concept_id": "probability_basics",
        "concept_name": "Probability Basics",
        "action": "review",
        "mastery": "weak",
        "score": 0.0,
        "priority": 1.75,
        "prerequisites_in_path": [],
        "reason": "Start here: ..."
      }
    ]
  }
}
```

**Errors:** `400 invalid_question_id`, `400 duplicate_answer`, `400 quiz_not_generated` (call `GET /api/quiz/{id}` first), `404 session_not_found`, `409 already_submitted`, `422 validation_error` (malformed body, e.g. option `"E"`).

---

### `GET /api/results/{session_id}`

Returns the stored `AssessmentResults` (identical to the submit response).

**Errors:** `404 session_not_found`, `409 assessment_not_submitted`.

---

## Schemas

### Concept
| Field | Type | Description |
|---|---|---|
| `id` | string | Stable snake_case ID. Unique within a session. |
| `name` | string | Display name. |
| `description` | string | 1–2 sentence summary. |
| `difficulty` | `"beginner" \| "intermediate" \| "advanced"` | |
| `prerequisites` | string[] | IDs of concepts that must be learned first. Always valid IDs; never self; graph is acyclic. |
| `source_type` | `"document" \| "inferred"` | `document` = covered in the notes; `inferred` = assumed prior knowledge. |
| `descendant_count` | int | Unique concepts that depend on this one, directly or indirectly. |
| `level` | int | Longest prerequisite chain from a root (roots = 0). Handy for layered layout. |

### Edge
| Field | Type | Description |
|---|---|---|
| `id` | string | `"{source}->{target}"` |
| `source` | string | Prerequisite concept ID (arrow tail). |
| `target` | string | Dependent concept ID (arrow head). |
| `relationship` | `"prerequisite"` | |

React Flow mapping: `nodes = concepts.map(c => ({ id: c.id, data: c, position }))`, `edges = edges.map(e => ({ id: e.id, source: e.source, target: e.target }))`.

### ProcessingStatus
| Field | Type | Description |
|---|---|---|
| `status` | `"completed"` | |
| `processing_mode` | `"direct" \| "chunked"` | `chunked` for documents over ~15k tokens. |
| `page_count` | int | |
| `estimated_tokens` | int | Approximate (≈ characters / 4). |
| `chunk_count` | int | 1 in direct mode. |
| `concept_count` | int | |
| `ai_requests_used` | int | Gemini calls used for analysis. |
| `quiz_status` | `"pending" \| "ready"` | |
| `warnings` | string[] | Non-fatal fixes applied to AI output (e.g. removed an invalid prerequisite). |

### QuizQuestion
| Field | Type | Description |
|---|---|---|
| `id` | string | `"q1"`, `"q2"`, … |
| `concept_id` | string | Concept being assessed. |
| `concept_name` | string | |
| `question` | string | |
| `options` | `{id: "A"\|"B"\|"C"\|"D", text: string}[]` | Always exactly 4. Exactly one is correct (hidden). |

### ConceptScore
| Field | Type | Description |
|---|---|---|
| `concept_id`, `concept_name` | string | |
| `correct`, `total` | int | `total` = 0 when unassessed. |
| `score` | float \| null | `correct / total`; **null** when unassessed (never 0). |
| `mastery` | `"strong" \| "developing" \| "weak" \| "unassessed"` | ≥ 0.80 strong, ≥ 0.50 developing, < 0.50 weak. Preliminary estimates. |

All concepts in the graph appear in `concept_scores`, ordered by `topological_order`.

### LearningGap
Assessed concepts classified `weak` or `developing`, sorted by `priority` (highest first).

| Field | Type | Description |
|---|---|---|
| `concept_id`, `concept_name` | string | |
| `score` | float | |
| `mastery` | `"weak" \| "developing"` | |
| `descendant_count` | int | |
| `downstream_concept_ids` | string[] | All unique dependents (topological order). |
| `priority` | float | `(1 − score) × (1 + 0.25 × descendant_count)` (weight configurable). |
| `reason` | string | Explanation built only from actual scores and graph relationships. |

### Recommendation
Gaps (`action: "review"`) plus unassessed prerequisites of gaps (`action: "verify"`, since the gap might originate there). Sorted by priority; `verify` items (priority `null`) come after `review` items.

| Field | Type |
|---|---|
| `rank` | int (1-based) |
| `concept_id`, `concept_name` | string |
| `action` | `"review" \| "verify"` |
| `score` | float \| null |
| `mastery` | Mastery |
| `descendant_count` | int |
| `priority` | float \| null |
| `reason` | string |

### LearningPath
`steps` contains the same concepts as `recommendations`, ordered so that **every concept appears after all of its prerequisites that are also in the path**. Among concepts that are ready at the same point, higher priority goes first. Strong concepts are never included. If there are no gaps, `steps` is empty and `summary` says so.

| Field | Type |
|---|---|
| `total_steps` | int |
| `summary` | string |
| `steps[].step` | int (1-based) |
| `steps[].concept_id`, `concept_name` | string |
| `steps[].action` | `"review" \| "verify"` |
| `steps[].mastery` | Mastery |
| `steps[].score` | float \| null |
| `steps[].priority` | float \| null |
| `steps[].prerequisites_in_path` | string[] — IDs of earlier steps this one builds on |
| `steps[].reason` | string |

---

## Errors

Every non-2xx response:
```json
{
  "error": {
    "code": "file_too_large",
    "message": "File exceeds the 10 MB limit.",
    "details": { "max_bytes": 10485760 }
  }
}
```

Switch on `error.code`; display `error.message` (safe for users).

| HTTP | `code` | When |
|---|---|---|
| 400 | `invalid_file_type` | Not a PDF (wrong extension or content). |
| 400 | `invalid_pdf` | Corrupted / unreadable PDF. |
| 400 | `empty_pdf` | PDF has no pages. |
| 400 | `encrypted_pdf` | Password-protected. |
| 400 | `no_extractable_text` | Scanned/image-only PDF. |
| 400 | `too_many_pages` | More than 50 pages. `details.max_pages`, `details.page_count`. |
| 400 | `invalid_question_id` | Submit referenced unknown question IDs. `details.invalid_question_ids`. |
| 400 | `duplicate_answer` | Same question answered twice. |
| 400 | `quiz_not_generated` | Submit before the quiz was fetched. |
| 404 | `session_not_found` | Unknown or expired session. |
| 404 | `not_found` | Unknown route. |
| 409 | `already_submitted` | Quiz already graded for this session. |
| 409 | `assessment_not_submitted` | Results requested before submitting. |
| 413 | `file_too_large` | Over 10 MB. |
| 413 | `document_too_long` | Text too long to analyze within the processing budget. |
| 422 | `validation_error` | Malformed request. `details.errors[]` lists field problems. |
| 429 | `rate_limited` | Too many requests (also returned when Gemini quota is exhausted). Has `Retry-After` header. |
| 502 | `ai_invalid_response` | Gemini repeatedly returned unusable output. Retry may help. |
| 503 | `ai_unavailable` | Gemini unreachable or timed out. |
| 503 | `ai_budget_exceeded` | Too many retries were needed for one document. Retry later. |
| 503 | `ai_not_configured` | Server has no Gemini key. |
| 500 | `internal_error` | Unexpected backend error. |

## Limits

| Limit | Default | Env var |
|---|---|---|
| File size | 10 MB | `MAX_FILE_SIZE_MB` |
| Pages | 50 | `MAX_PAGES` |
| Document tokens (approx) | 40,000 | `MAX_DOCUMENT_TOKENS` |
| Chunks per document | 10 | `MAX_CHUNKS` |
| `/api/analyze` per client IP | 5 / minute | `RATE_LIMIT_ANALYZE_PER_MINUTE` |
| Other endpoints per client IP | 120 / minute | `RATE_LIMIT_DEFAULT_PER_MINUTE` |
| Session lifetime | 120 min | `SESSION_TTL_MINUTES` |

## Mock answer key

In `AI_MODE=mock`, the correct options for `q1`–`q12` are:
`B, D, C, A, B, A, D, C, A, B, C, D`

## Changelog

- **1.0.0 (2026-10-10)** — Initial contract.
