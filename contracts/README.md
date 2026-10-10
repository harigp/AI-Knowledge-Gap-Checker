# API contracts

Example payloads for every endpoint. They are **generated from the backend's
Pydantic models** by `backend/make_contracts.py`, so don't edit them by hand.
If `backend/models.py` changes, regenerate with:

    cd backend && python make_contracts.py

| Endpoint | File |
|---|---|
| `POST /api/analyze` (multipart form, field `file`) | response: `mock_analyze.json` |
| `GET /api/graph/{sessionId}` | `mock_graph.json` |
| `GET /api/quiz/{sessionId}` | `mock_quiz.json` |
| `POST /api/quiz/{sessionId}/submit` | request: `mock_submit_request.json`, response: `mock_results.json` |
| `GET /api/results/{sessionId}` | `mock_results.json` |

## Conventions

- **Field names are snake_case.** Keep them as-is in TypeScript.
- **Edge direction:** `prerequisite_ids` lists a concept's prerequisites. Draw an edge
  from each prerequisite to the concept (`probability` -> `statistics`).
- **Quiz answers are indices 0-3** into `options`. The public quiz has no answer keys
  and `explanation` is always `""`.
- **Scores are fractions from 0 to 1**, not percentages.
- **`concept_scores` has one entry for every concept.** `score: null` with
  `classification: "unknown"` means not assessed.
- **Colors:** `strong` = green, `developing` = yellow, `weak` = red, `unknown` = gray.
- **`recommendations` is already in study order.** Render it as-is (`position` is 1-based).
  Strong and unassessed concepts are intentionally left out.
- `session_status` values: `created`, `graph_ready`, `quiz_ready`, `completed`, `failed`.

## Errors (proposed, FastAPI teammate to confirm)

Error bodies use FastAPI's default shape: `{"detail": "human-readable message"}`.

- `404`: unknown session id
- `409`: results requested before the quiz was submitted
- `400` / `413` / `422`: bad upload (wrong type, too large, empty, scanned PDF)

## What the sample data shows

A student who is shaky on **Probability** (0/2, red) but fine on **Derivatives** and
**Gradient Descent** (2/2, green). Probability has 3 downstream concepts, so it tops the
study path. Five concepts were never quizzed and stay gray.