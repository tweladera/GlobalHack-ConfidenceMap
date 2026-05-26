Show the current project status for Confidence Map.

Read `STATUS.md` and summarize:
1. Last checkpoint (date, session, test results)
2. Phase progress (which phases are complete, which are pending)
3. Known issues
4. Next action

Then run the quick verification commands:
- `cd backend && ANTHROPIC_API_KEY=test uv run pytest --no-header -q 2>&1 | tail -3`
- `cd backend && uv run ruff check confidence_map/ 2>&1`
- `cd backend && uv run mypy --strict confidence_map/ 2>&1 | tail -2`

Report the live state of each check alongside the STATUS.md summary.
