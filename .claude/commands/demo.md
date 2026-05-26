Launch the Confidence Map demo in DEMO_MODE (no API key required, $0 cost).

Steps:
1. Verify `backend/.env` exists and contains `DEMO_MODE=true`. If not, remind the user to set it.
2. Run `make demo` from the project root to start backend (:8000) + frontend (:3000) in parallel.
3. Tell the user to open http://localhost:3000, select "NovaBank · Pagos" or "NovaBank · Auth MFA", and click "Run Analysis".
4. Expected: analysis completes in ~5 seconds with 6 agents activating in sequence on the map.

If `make demo` is not available, use:
- Terminal 1: `cd backend && DEMO_MODE=true uv run uvicorn confidence_map.main:app --reload`
- Terminal 2: `cd frontend && pnpm dev`
