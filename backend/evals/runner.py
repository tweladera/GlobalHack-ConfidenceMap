"""Eval runner: runs agent subsets against golden specs and checks recall.

Usage (from backend/):
    ANTHROPIC_API_KEY=sk-... uv run python -m evals
    ANTHROPIC_API_KEY=sk-... uv run python -m evals --spec simplebank

Each golden spec specifies which agents to run and what issues they must find.
A DetectionCriteria is satisfied if any keyword appears (case-insensitive) in
the title or description of a finding produced by the named agent (or any
agent when agent_id is None).

The suite exits 0 if every spec meets its min_recall threshold, 1 otherwise.
"""

from __future__ import annotations

import asyncio
import importlib
import time
from dataclasses import dataclass

from confidence_map.models.findings import AgentResult, Finding
from evals.golden_specs import DetectionCriteria, GoldenSpec


# ── Detection logic ───────────────────────────────────────────────────────────


def _text(f: Finding) -> str:
    return f"{f.title} {f.description}".lower()


def _detect(
    criteria: DetectionCriteria,
    findings: list[Finding],
) -> Finding | None:
    """Return the first finding that satisfies the criteria, or None."""
    candidates = (
        [f for f in findings if f.agent_id == criteria.agent_id]
        if criteria.agent_id
        else findings
    )
    for f in candidates:
        text = _text(f)
        if any(kw.lower() in text for kw in criteria.keywords):
            return f
    return None


# ── Agent runner ──────────────────────────────────────────────────────────────


async def _run_agent(agent_id: str, spec: str, architecture: str) -> AgentResult:
    """Import and run a single agent module, return its AgentResult."""
    module = importlib.import_module(f"confidence_map.agents.{agent_id}")
    result: AgentResult = await module.run(
        spec=spec,
        architecture=architecture,
        context="",
        spec_findings=None,
    )
    return result


async def _run_spec(golden: GoldenSpec) -> "SpecReport":
    """Run all required agents for a golden spec and return detection results."""
    t0 = time.monotonic()

    tasks = [
        asyncio.create_task(_run_agent(aid, golden.spec, golden.architecture))
        for aid in golden.agents_to_run
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_findings: list[Finding] = []
    agent_summaries: list[str] = []
    for aid, r in zip(golden.agents_to_run, results):
        if isinstance(r, Exception):
            agent_summaries.append(f"{aid}: ERROR ({r})")
        else:
            all_findings.extend(r.findings)
            agent_summaries.append(f"{aid}: {len(r.findings)} findings")

    elapsed = time.monotonic() - t0
    detections: list[Detection] = []
    for c in golden.criteria:
        found = _detect(c, all_findings)
        detections.append(Detection(criteria=c, match=found))

    return SpecReport(
        golden=golden,
        detections=detections,
        agent_summaries=agent_summaries,
        elapsed=elapsed,
    )


# ── Report dataclasses ────────────────────────────────────────────────────────


@dataclass
class Detection:
    criteria: DetectionCriteria
    match: Finding | None

    @property
    def found(self) -> bool:
        return self.match is not None


@dataclass
class SpecReport:
    golden: GoldenSpec
    detections: list[Detection]
    agent_summaries: list[str]
    elapsed: float

    @property
    def recall(self) -> float:
        if not self.detections:
            return 1.0
        return sum(1 for d in self.detections if d.found) / len(self.detections)

    @property
    def passed(self) -> bool:
        return self.recall >= self.golden.min_recall


# ── Console output ────────────────────────────────────────────────────────────

_CYAN   = "\033[36m"
_GREEN  = "\033[32m"
_RED    = "\033[31m"
_YELLOW = "\033[33m"
_BOLD   = "\033[1m"
_RESET  = "\033[0m"
_DIM    = "\033[2m"

_W = 62  # report width


def _print_report(reports: list[SpecReport]) -> None:
    print()
    print(f"{_BOLD}{'═' * _W}")
    print(f"  CONFIDENCE MAP — EVAL SUITE")
    print(f"{'═' * _W}{_RESET}")

    for i, rep in enumerate(reports, 1):
        g = rep.golden
        print()
        print(f"{_BOLD}[{i}/{len(reports)}] {g.name}{_RESET}")
        print(f"  {_DIM}{g.description}{_RESET}")
        for s in rep.agent_summaries:
            print(f"  {_DIM}→ {s}{_RESET}")
        print(f"  {_DIM}({rep.elapsed:.1f}s){_RESET}")
        print()

        for d in rep.detections:
            if d.found:
                assert d.match is not None
                snippet = d.match.title[:60].rstrip()
                print(f"  {_GREEN}✓{_RESET} {d.criteria.label}")
                print(f"    {_DIM}→ [{d.match.agent_id}] \"{snippet}\"{_RESET}")
            else:
                print(f"  {_RED}✗{_RESET} {d.criteria.label}")
                agent_hint = f" (expected: {d.criteria.agent_id})" if d.criteria.agent_id else ""
                print(f"    {_DIM}not detected{agent_hint}{_RESET}")

        found = sum(1 for d in rep.detections if d.found)
        total = len(rep.detections)
        pct = rep.recall * 100
        threshold_pct = g.min_recall * 100
        status_color = _GREEN if rep.passed else _RED
        status_label = "PASS" if rep.passed else "FAIL"
        print()
        print(
            f"  {_BOLD}Recall: {found}/{total} ({pct:.0f}%)"
            f"  min={threshold_pct:.0f}%"
            f"  {status_color}{status_label}{_RESET}"
        )

    # Overall summary
    total_criteria = sum(len(r.detections) for r in reports)
    total_found = sum(sum(1 for d in r.detections if d.found) for r in reports)
    all_pass = all(r.passed for r in reports)
    overall_color = _GREEN if all_pass else _RED
    overall_label = "ALL SPECS PASSED" if all_pass else "ONE OR MORE SPECS FAILED"

    print()
    print(f"{_BOLD}{'─' * _W}{_RESET}")
    print(
        f"{_BOLD}Overall: {total_found}/{total_criteria} criteria detected"
        f" ({total_found / total_criteria * 100:.0f}%)"
        f"  {overall_color}{overall_label}{_RESET}"
    )
    print(f"{_BOLD}{'─' * _W}{_RESET}")
    print()


# ── Public entry point ────────────────────────────────────────────────────────


async def run_evals(spec_filter: str | None = None) -> bool:
    """Run the full eval suite and return True if all specs pass.

    Args:
        spec_filter: Optional name substring to run only matching specs.
    """
    from evals.golden_specs import GOLDEN_SPECS

    specs = (
        [s for s in GOLDEN_SPECS if spec_filter.lower() in s.name.lower()]
        if spec_filter
        else GOLDEN_SPECS
    )

    if not specs:
        print(f"{_RED}No specs match filter: {spec_filter!r}{_RESET}")
        return False

    print(f"\n{_CYAN}Running {len(specs)} golden spec(s)...{_RESET}")
    print(f"{_DIM}This calls the real Claude API and may take several minutes.{_RESET}")

    reports: list[SpecReport] = []
    for golden in specs:
        print(f"\n{_DIM}→ {golden.name} ({', '.join(golden.agents_to_run)})...{_RESET}")
        report = await _run_spec(golden)
        reports.append(report)

    _print_report(reports)
    return all(r.passed for r in reports)
