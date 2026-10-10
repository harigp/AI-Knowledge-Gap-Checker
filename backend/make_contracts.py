"""
make_contracts.py: generates the shared example JSON from the real Pydantic models.

Run from backend/ whenever models.py changes:

    python make_contracts.py

Writes:
    ../contracts/*.json                     shared with the whole team (no answer keys)
    ../contracts/README.md
    tests/fixtures/mock_quiz_private.json   BACKEND ONLY (includes answer keys)

Because every payload is built with the real models, the examples can't drift
from the code. The results are computed by the real gap_analyzer, so they are
mathematically consistent with the graph and the answers.

Demo story baked into the data: a student who is shaky on Probability
(a foundational concept) but fine on Derivatives and Gradient Descent.
"""

import json
from pathlib import Path

from gap_analyzer import build_results, make_concept_score
from models import (
    AnalyzeResponse,
    Concept,
    GraphResponse,
    QuizQuestionPrivate,
    QuizResponse,
    SubmitRequest,
)

BACKEND = Path(__file__).resolve().parent
CONTRACTS = BACKEND.parent / "contracts"
FIXTURES = BACKEND / "tests" / "fixtures"

SESSION_ID = "3f2a9c1e7b4d4e8a9c0d5b6e1f2a3b4c"
DOCUMENT_NAME = "intro_to_machine_learning.pdf"


# ---------- Graph: 10 concepts ----------

def C(id, name, description, difficulty, source_type, prereqs):
    return Concept(
        id=id, name=name, description=description, difficulty=difficulty,
        source_type=source_type, prerequisite_ids=prereqs,
    )


CONCEPTS = [
    C("algebra", "Basic Algebra", "Manipulating equations and expressions with variables.",
      "beginner", "inferred", []),
    C("functions", "Functions", "Mapping inputs to outputs and reading function notation.",
      "beginner", "inferred", ["algebra"]),
    C("derivatives", "Derivatives", "The instantaneous rate of change of a function.",
      "intermediate", "direct", ["functions"]),
    C("probability", "Probability", "Quantifying how likely uncertain events are.",
      "beginner", "direct", []),
    C("statistics", "Statistics", "Summarizing and interpreting data using means, variance, and distributions.",
      "intermediate", "direct", ["probability"]),
    C("statistical_inference", "Statistical Inference", "Drawing conclusions about a population from a sample.",
      "advanced", "direct", ["statistics"]),
    C("linear_algebra", "Linear Algebra", "Working with vectors and matrices.",
      "intermediate", "direct", ["algebra"]),
    C("linear_regression", "Linear Regression", "Modeling the relationship between variables with a line.",
      "intermediate", "direct", ["statistics", "linear_algebra"]),
    C("loss_functions", "Loss Functions", "Measuring how far a model's predictions are from the truth.",
      "intermediate", "direct", ["functions"]),
    C("gradient_descent", "Gradient Descent", "Minimizing a loss by repeatedly stepping against the gradient.",
      "advanced", "direct", ["derivatives", "loss_functions"]),
]


# ---------- Quiz: 10 questions over 5 concepts ----------

def Q(id, concept_id, question, options, correct_index, explanation):
    return QuizQuestionPrivate(
        id=id, concept_id=concept_id, question=question, options=options,
        correct_index=correct_index, explanation=explanation,
    )


QUESTIONS = [
    Q("q1", "probability", "A fair six-sided die is rolled. What is the probability of rolling an even number?",
      ["1/6", "1/3", "1/2", "2/3"], 2,
      "Three of the six faces (2, 4, 6) are even, so the probability is 3/6 = 1/2."),
    Q("q2", "probability", "Two fair coins are flipped. What is the probability that both land heads?",
      ["1/4", "1/2", "1/3", "3/4"], 0,
      "The flips are independent, so multiply: 1/2 x 1/2 = 1/4."),
    Q("q3", "statistics", "What is the mean of the data set 2, 4, 6, 8?",
      ["4", "5", "6", "20"], 1,
      "The sum is 20 and there are 4 values, so the mean is 20/4 = 5."),
    Q("q4", "statistics", "Which measure of spread is the square root of the variance?",
      ["Median", "Range", "Standard deviation", "Mode"], 2,
      "Standard deviation is defined as the square root of the variance."),
    Q("q5", "derivatives", "What is the derivative of f(x) = x^2?",
      ["x", "x^2", "2", "2x"], 3,
      "By the power rule, d/dx of x^2 is 2x."),
    Q("q6", "derivatives", "What does the derivative of a function at a point represent?",
      ["The area under the curve up to that point",
       "The instantaneous rate of change at that point",
       "The maximum value of the function",
       "The average of the function's values"], 1,
      "The derivative gives the slope of the tangent line, the instantaneous rate of change."),
    Q("q7", "linear_regression", "In simple linear regression, what does the slope represent?",
      ["The expected change in y for a one-unit increase in x",
       "The predicted value of y when x is 0",
       "The average of all y values",
       "The number of data points"], 0,
      "The slope is how much the predicted y changes when x increases by one unit."),
    Q("q8", "linear_regression", "Which quantity does ordinary least squares regression minimize?",
      ["The largest single residual", "The sum of absolute residuals",
       "The number of outliers", "The sum of squared residuals"], 3,
      "Ordinary least squares chooses the line that minimizes the sum of squared residuals."),
    Q("q9", "gradient_descent", "In gradient descent, in which direction is each parameter update taken?",
      ["Along the gradient", "Opposite the gradient", "Perpendicular to the gradient", "In a random direction"], 1,
      "The gradient points uphill, so gradient descent steps in the opposite direction to reduce the loss."),
    Q("q10", "gradient_descent", "What can happen if the learning rate in gradient descent is set too large?",
      ["The loss function changes shape", "The gradient becomes zero",
       "Training always converges faster", "The updates can overshoot the minimum and diverge"], 3,
      "Steps that are too large can jump past the minimum and make the loss grow instead of shrink."),
]

# Student answers: shaky on probability (0/2), mixed on statistics and regression (1/2),
# solid on derivatives and gradient descent (2/2).
ANSWERS = {
    "q1": 1, "q2": 1,   # probability: both wrong
    "q3": 1, "q4": 0,   # statistics: first right, second wrong
    "q5": 3, "q6": 1,   # derivatives: both right
    "q7": 0, "q8": 1,   # linear regression: first right, second wrong
    "q9": 1, "q10": 3,  # gradient descent: both right
}


# ---------- Building the payloads ----------

def per_concept_scores():
    """Quick stand-in grader for the fixtures. The real one is grader.py.

    Contract: concept_scores has ONE entry per concept in the graph. Concepts with
    no questions get total=0, score=null, classification='unknown' (gray).
    """
    totals = {c.id: [0, 0] for c in CONCEPTS}  # [correct, total]
    for q in QUESTIONS:
        totals[q.concept_id][1] += 1
        if ANSWERS[q.id] == q.correct_index:
            totals[q.concept_id][0] += 1
    return [make_concept_score(cid, c, t) for cid, (c, t) in totals.items()]


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = payload.model_dump(mode="json") if hasattr(payload, "model_dump") else payload
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path}")


README = """\
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
"""


def main() -> None:
    questions_public = [q.to_public() for q in QUESTIONS]
    results = build_results(SESSION_ID, per_concept_scores(), CONCEPTS)

    write_json(CONTRACTS / "mock_analyze.json", AnalyzeResponse(
        session_id=SESSION_ID, document_name=DOCUMENT_NAME,
        status="quiz_ready", concepts=CONCEPTS,
    ))
    write_json(CONTRACTS / "mock_graph.json", GraphResponse(
        session_id=SESSION_ID, document_name=DOCUMENT_NAME, concepts=CONCEPTS,
    ))
    write_json(CONTRACTS / "mock_quiz.json", QuizResponse(
        session_id=SESSION_ID, questions=questions_public,
    ))
    write_json(CONTRACTS / "mock_submit_request.json", SubmitRequest(answers=ANSWERS))
    write_json(CONTRACTS / "mock_results.json", results)

    (CONTRACTS / "README.md").write_text(README, encoding="utf-8")
    print(f"wrote {CONTRACTS / 'README.md'}")

    # Backend-only: includes correct answers. Deliberately NOT in contracts/.
    write_json(FIXTURES / "mock_quiz_private.json", [q.model_dump(mode="json") for q in QUESTIONS])


if __name__ == "__main__":
    main()