"""Generate samples/sample_lecture.pdf, a short text-based lecture for manual testing."""

from pathlib import Path

import pymupdf

PAGES = [
    """Lecture 7: Simple Linear Regression

1. Why regression?
Regression lets us model how a response variable y changes with a predictor x. Before starting, make sure
you are comfortable with linear functions y = mx + b, where m is the slope and b is the intercept.

2. Review: describing data
The sample mean summarizes the center of a dataset. The variance and standard deviation describe how spread
out the observations are around the mean. Outliers can strongly affect the mean and standard deviation.

3. Correlation
The correlation coefficient r measures the strength and direction of a linear relationship between two
variables. It ranges from -1 to 1. Values near 0 indicate little linear association. Correlation does not
imply causation: a lurking variable can produce a strong correlation between unrelated quantities.""",
    """4. The simple linear regression model
We model y = b0 + b1 x + e, where b0 is the intercept, b1 the slope, and e a random error term with mean zero.
The slope b1 is the expected change in y for a one-unit increase in x.

5. Least squares estimation
The fitted line minimizes the sum of squared residuals, where a residual is the observed value minus the
predicted value. The least squares slope equals r multiplied by the ratio of the standard deviations of y and x.

6. Inference for the slope
Treating the errors as random variables lets us quantify uncertainty in b1. Using probability distributions,
we build confidence intervals and run hypothesis tests of H0: b1 = 0. A small p-value is evidence of a linear
relationship. Checking residual plots helps verify the model assumptions.""",
]


def main() -> None:
    out = Path(__file__).resolve().parent.parent / "samples" / "sample_lecture.pdf"
    doc = pymupdf.open()
    for text in PAGES:
        doc.new_page().insert_textbox(pymupdf.Rect(60, 60, 550, 790), text, fontsize=11)
    doc.save(out)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
