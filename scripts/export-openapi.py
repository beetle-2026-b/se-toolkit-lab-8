"""Export the OpenAPI schema from the FastAPI app to a JSON file."""

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = REPO_ROOT / "backend" / "openapi.json"

# Enable all conditional routers so the full schema is exported
os.environ.setdefault("LMS_API_KEY", "dummy")
os.environ.setdefault("BACKEND_ENABLE_INTERACTIONS", "true")
os.environ.setdefault("BACKEND_ENABLE_LEARNERS", "true")

from app.main import app


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check that the file is up to date instead of writing it",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output file path (default: %(default)s)",
    )
    args = parser.parse_args()

    schema = app.openapi()
    new_content = json.dumps(schema, indent=2) + "\n"

    if args.check:
        if not args.output.exists():
            print(f"ERROR: {args.output} does not exist.", file=sys.stderr)
            print("Run `uv run poe export-openapi` to generate it.", file=sys.stderr)
            raise SystemExit(1)
        old_content = args.output.read_text()
        if old_content != new_content:
            print(f"ERROR: {args.output} is out of date.", file=sys.stderr)
            print(
                "Run `uv run poe export-openapi` and commit the result.",
                file=sys.stderr,
            )
            raise SystemExit(1)
        print("openapi.json is up to date.")
        return

    args.output.write_text(new_content)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
