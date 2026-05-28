"""Entry point for `python -m evals`.

Usage (from backend/):
    ANTHROPIC_API_KEY=sk-ant-... uv run python -m evals
    ANTHROPIC_API_KEY=sk-ant-... uv run python -m evals --spec simplebank
    ANTHROPIC_API_KEY=sk-ant-... uv run python -m evals --spec medipay

Options:
    --spec <name>    Run only the spec whose name contains this substring
                     (case-insensitive). Omit to run all golden specs.
"""

from __future__ import annotations

import asyncio
import sys


def _parse_spec_filter() -> str | None:
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--spec" and i + 1 < len(args):
            return args[i + 1]
    return None


def main() -> None:
    # Validate API key before spending time on imports
    import os

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or api_key == "test":
        print(
            "\n\033[31m✗ ANTHROPIC_API_KEY is required for evals.\033[0m\n"
            "  Evals call the real Claude API and are not free.\n"
            "\n"
            "  Usage:\n"
            "    ANTHROPIC_API_KEY=sk-ant-... make eval\n"
            "    ANTHROPIC_API_KEY=sk-ant-... uv run python -m evals\n"
        )
        sys.exit(1)

    from evals.runner import run_evals

    spec_filter = _parse_spec_filter()
    passed = asyncio.run(run_evals(spec_filter=spec_filter))
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
