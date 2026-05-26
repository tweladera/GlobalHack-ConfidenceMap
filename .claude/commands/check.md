Run all quality gates for this project sequentially and report results.

Execute the following commands from the project root:

1. `cd backend && uv run ruff check confidence_map/` — linting (0 errors required)
2. `cd backend && uv run mypy --strict confidence_map/` — type check (0 errors required)
3. `cd backend && ANTHROPIC_API_KEY=test uv run pytest --no-header -q` — 42 tests, ≥80% coverage
4. `cd frontend && pnpm exec tsc --noEmit` — TypeScript check (no output = ok)

Report the result of each gate clearly. If any gate fails, show the error and suggest a fix before continuing.
