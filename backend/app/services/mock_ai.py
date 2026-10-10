"""Deterministic stand-in for Gemini (AI_MODE=mock).

Returns a fixed statistics/regression concept graph and quiz so the frontend can be built and
demoed without an API key. Output goes through the same validation as real Gemini output.
Option order is fixed, so the answer key documented in API_CONTRACT.md stays stable:
q1-q12 = B, D, C, A, B, A, D, C, A, B, C, D.
"""

from __future__ import annotations

import json

from pydantic import BaseModel

from app.services.gemini_client import RequestBudget

MOCK_CONCEPTS = [
    {"id": "algebra_fundamentals", "name": "Algebra Fundamentals",
     "description": "Manipulating equations and interpreting linear functions, slopes and intercepts.",
     "difficulty": "beginner", "prerequisites": [], "source_type": "inferred"},
    {"id": "probability_basics", "name": "Probability Basics",
     "description": "Sample spaces, events, and the rules for computing probabilities.",
     "difficulty": "beginner", "prerequisites": [], "source_type": "inferred"},
    {"id": "descriptive_statistics", "name": "Descriptive Statistics",
     "description": "Summarizing data with measures of center and spread such as mean, variance and standard deviation.",
     "difficulty": "beginner", "prerequisites": ["algebra_fundamentals"], "source_type": "document"},
    {"id": "random_variables", "name": "Random Variables",
     "description": "Numeric outcomes of random processes, their distributions, expectation and variance.",
     "difficulty": "intermediate", "prerequisites": ["probability_basics"], "source_type": "document"},
    {"id": "correlation", "name": "Correlation",
     "description": "Measuring the strength and direction of a linear relationship between two variables.",
     "difficulty": "intermediate", "prerequisites": ["descriptive_statistics"], "source_type": "document"},
    {"id": "hypothesis_testing", "name": "Hypothesis Testing",
     "description": "Using sample data to evaluate claims about populations with test statistics and p-values.",
     "difficulty": "intermediate", "prerequisites": ["random_variables", "descriptive_statistics"],
     "source_type": "document"},
    {"id": "simple_linear_regression", "name": "Simple Linear Regression",
     "description": "Modeling a response variable as a linear function of a single predictor.",
     "difficulty": "intermediate", "prerequisites": ["correlation", "algebra_fundamentals"],
     "source_type": "document"},
    {"id": "least_squares_estimation", "name": "Least Squares Estimation",
     "description": "Choosing regression coefficients that minimize the sum of squared residuals.",
     "difficulty": "advanced", "prerequisites": ["simple_linear_regression"], "source_type": "document"},
    {"id": "regression_inference", "name": "Regression Inference",
     "description": "Confidence intervals and hypothesis tests for regression coefficients.",
     "difficulty": "advanced", "prerequisites": ["least_squares_estimation", "hypothesis_testing"],
     "source_type": "document"},
]


def _q(concept_id, question, options, correct, explanation):
    return {"concept_id": concept_id, "question": question, "options": options,
            "correct_option_index": "ABCD".index(correct), "explanation": explanation}


MOCK_QUESTIONS = [
    _q("algebra_fundamentals", "What is the slope of the line y = 3x + 2?", ["2", "3", "5", "3/2"], "B",
       "In y = mx + b the slope is m, so the slope is 3."),
    _q("algebra_fundamentals", "If 2x + 4 = 10, what is x?", ["7", "2", "6", "3"], "D",
       "Subtract 4 to get 2x = 6, then divide by 2: x = 3."),
    _q("probability_basics", "A fair die is rolled once. What is the probability of rolling an even number?",
       ["1/6", "1/3", "1/2", "2/3"], "C",
       "Three of the six equally likely outcomes (2, 4, 6) are even, so P = 3/6 = 1/2."),
    _q("probability_basics", "If P(A) = 0.3, what is P(not A)?", ["0.7", "0.3", "1.3", "0.03"], "A",
       "Complementary events sum to 1, so P(not A) = 1 - 0.3 = 0.7."),
    _q("descriptive_statistics", "Which measure is most affected by a single extreme outlier?",
       ["Median", "Mean", "Mode", "Interquartile range"], "B",
       "The mean uses every value's magnitude, so one extreme value pulls it strongly."),
    _q("descriptive_statistics", "What does the standard deviation describe?",
       ["How spread out values are around the mean", "The most common value", "The middle value",
        "The difference between max and min"], "A",
       "Standard deviation measures the typical distance of values from the mean."),
    _q("random_variables", "What is the expected value of a fair six-sided die roll?", ["3", "4", "6", "3.5"], "D",
       "E[X] = (1+2+3+4+5+6)/6 = 21/6 = 3.5."),
    _q("random_variables", "If Var(X) = 4, what is Var(3X)?", ["12", "4", "36", "7"], "C",
       "Scaling a variable by a multiplies its variance by a squared: 9 x 4 = 36."),
    _q("correlation", "A correlation coefficient of r = -0.9 indicates:",
       ["A strong negative linear relationship", "A weak negative relationship", "No relationship",
        "A strong positive relationship"], "A",
       "Values near -1 indicate a strong linear relationship in which one variable decreases as the other increases."),
    _q("correlation", "Which statement about correlation is true?",
       ["Correlation proves causation", "Correlation does not by itself imply causation",
        "Correlation is always between 0 and 1", "Correlation measures any non-linear relationship"], "B",
       "Correlation measures linear association only; a confounding variable can create correlation without causation."),
    _q("simple_linear_regression", "In the model y = b0 + b1*x, what does b1 represent?",
       ["The predicted y when x = 0", "The correlation between x and y",
        "The expected change in y for a one-unit increase in x", "The residual error"], "C",
       "b1 is the slope: the expected change in the response for each one-unit increase in the predictor."),
    _q("simple_linear_regression", "What is a residual in linear regression?",
       ["The slope of the fitted line", "The predicted value of y", "The value of x for which y = 0",
        "The difference between an observed y and its predicted value"], "D",
       "A residual is observed minus predicted: e = y - y_hat."),
]


class MockJsonGenerator:
    async def generate(self, *, task: str, system: str, prompt: str, schema: type[BaseModel],
                       budget: RequestBudget) -> str:
        budget.consume()
        if task == "generate_quiz":
            return json.dumps({"questions": MOCK_QUESTIONS})
        return json.dumps({"concepts": MOCK_CONCEPTS})
