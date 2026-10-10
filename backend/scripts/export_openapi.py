"""Write backend/openapi.json (for frontend TypeScript type generation)."""

import json
import os
from pathlib import Path

os.environ.setdefault("AI_MODE", "mock")

from app.main import create_app  # noqa: E402


def main() -> None:
    out = Path(__file__).resolve().parent.parent / "openapi.json"
    out.write_text(json.dumps(create_app().openapi(), indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
