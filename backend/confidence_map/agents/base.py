"""Base agent: Claude tool-use call that returns structured findings."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, cast

import anthropic

from confidence_map.core.settings import get_settings
from confidence_map.models.findings import AgentResult, AgentStatus, ConfidenceLevel, Finding

logger = logging.getLogger(__name__)

# ── Tool schema ───────────────────────────────────────────────────────────────

_FINDING_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Short, actionable title (max 100 chars)"},
        "description": {"type": "string", "description": "Detailed explanation of the finding"},
        "confidence": {
            "type": "string",
            "enum": ["green", "yellow", "red"],
            "description": (
                "green=explicitly defined, yellow=reasonably inferred, "
                "red=missing/contradictory/high uncertainty"
            ),
        },
        "confidence_score": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": (
                "Numeric confidence that must align with the chosen level: "
                "green -> 0.60-1.00, yellow -> 0.30-0.75, red -> 0.00-0.45. "
                "Do NOT assign a high score to a red finding."
            ),
        },
        "evidence": {
            "type": "string",
            "description": "Exact quote or specific reference from the spec",
        },
        "assumptions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "What is being assumed (empty if nothing)",
        },
        "needs_validation": {
            "type": "array",
            "items": {"type": "string"},
            "description": "What needs clarification or validation",
        },
        "recommended_action": {
            "type": "string",
            "description": (
                "Concrete next step: what the team should do"
                " to address this finding (1-2 sentences)"
            ),
        },
        "category": {
            "type": "string",
            "description": "Category: ambiguity|contradiction|risk|gap|accessibility|cost|pattern",
        },
    },
    "required": [
        "title",
        "description",
        "confidence",
        "confidence_score",
        "evidence",
        "category",
    ],
}

REPORT_FINDINGS_TOOL: anthropic.types.ToolParam = {
    "name": "report_findings",
    "description": "Report all findings from the analysis with explicit confidence levels",
    "input_schema": {
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "items": _FINDING_SCHEMA,
                "minItems": 1,
            },
            "summary": {
                "type": "string",
                "description": "One-paragraph narrative summary of all findings for screen readers",
            },
        },
        "required": ["findings", "summary"],
    },
}


# ── Guardrails ────────────────────────────────────────────────────────────────

# Expected confidence_score ranges per level.
# Scores outside these bounds indicate a model calibration mismatch.
_SCORE_BOUNDS: dict[str, tuple[float, float]] = {
    "green":  (0.60, 1.00),
    "yellow": (0.30, 0.75),
    "red":    (0.00, 0.45),
}

_EMPTY_EVIDENCE_PLACEHOLDER = "No direct quote provided — see finding description for context."


def _apply_guardrails(findings: list[Finding], *, agent_id: str) -> list[Finding]:
    """Apply post-extraction guardrails and return corrected findings.

    Rules enforced (warnings logged, no exception raised):
    1. Score-level alignment: clamp score to the expected range for the confidence level.
    2. Empty evidence: substitute a placeholder when the model omits a quote.
    3. All-green distribution: warn when every finding is green (possible under-analysis).
    """
    corrected: list[Finding] = []

    for f in findings:
        updates: dict[str, Any] = {}

        # Guardrail 1 — score must fall within the bounds for its confidence level
        lo, hi = _SCORE_BOUNDS.get(f.confidence, (0.0, 1.0))
        if not (lo <= f.confidence_score <= hi):
            clamped = round(max(lo, min(hi, f.confidence_score)), 3)
            logger.warning(
                "[guardrail] %s — score %.2f out of range for level '%s' [%.2f-%.2f]; "
                "clamped to %.3f. Finding: %r",
                agent_id, f.confidence_score, f.confidence, lo, hi, clamped, f.title,
            )
            updates["confidence_score"] = clamped

        # Guardrail 2 — evidence cannot be empty
        if not f.evidence.strip():
            logger.warning(
                "[guardrail] %s — finding %r has empty evidence; substituting placeholder.",
                agent_id, f.title,
            )
            updates["evidence"] = _EMPTY_EVIDENCE_PLACEHOLDER

        corrected.append(f.model_copy(update=updates) if updates else f)

    # Guardrail 3 — distribution sanity: all-green output on a multi-finding result is suspicious
    if len(corrected) > 2 and all(f.confidence == "green" for f in corrected):
        logger.warning(
            "[guardrail] %s — all %d findings are GREEN; verify the spec is not trivially simple.",
            agent_id, len(corrected),
        )

    return corrected


# ── Shared Blackboard helper ───────────────────────────────────────────────────


def format_spec_findings(findings: list[Finding]) -> str:
    """Render Spec Analyst findings as an XML context block for Phase-2 agents.

    Each finding is rendered as a one-liner so agents can orient themselves
    without duplicating work already done by the Spec Analyst.
    """
    if not findings:
        return ""
    lines = [
        "<spec_analyst_context>",
        "The Spec Analyst has already identified the following issues.",
        "Use this as shared context to focus on your domain and avoid duplicating these findings:",
        "",
    ]
    for f in findings:
        score_pct = round(f.confidence_score * 100)
        lines.append(f"  [{f.confidence.upper()} | {score_pct}%] {f.title}")
        truncated = f.description[:160].rstrip()
        suffix = "..." if len(f.description) > 160 else ""
        lines.append(f"    {truncated}{suffix}")
        lines.append("")
    lines.append("</spec_analyst_context>")
    return "\n".join(lines) + "\n\n"


# ── Retry policy ──────────────────────────────────────────────────────────────

_MAX_RETRIES = 2          # total extra attempts after the first failure
_RETRY_BASE_DELAY = 2.0   # seconds — actual delay = base * 2^attempt (2s, 4s)


def _extract_thinking(content: list[anthropic.types.ContentBlock]) -> str:
    """Concatenate all thinking blocks from an extended-thinking response.

    When ENABLE_THINKING=false, the response has no thinking blocks and this
    returns an empty string with no overhead.
    """
    parts: list[str] = []
    for block in content:
        if block.type == "thinking":
            text = getattr(block, "thinking", "")
            if text:
                parts.append(text)
    return "\n\n---\n\n".join(parts)


async def _make_api_call(
    client: anthropic.AsyncAnthropic,
    *,
    agent_id: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    enable_thinking: bool = False,
    thinking_budget: int = 5000,
) -> anthropic.types.Message:
    """Call the Claude API with exponential backoff for rate limits and 5xx errors.

    When ``enable_thinking`` is True, the ENABLE_THINKING feature flag is active:
    the call includes a ``thinking`` block that lets Claude reason before producing
    findings. This increases latency and cost but improves accuracy on complex specs.

    Raises the original exception once all retries are exhausted so that
    ``call_agent`` can handle it and populate the AgentResult error field.
    """
    for attempt in range(_MAX_RETRIES + 1):
        try:
            if enable_thinking:
                response = await client.messages.create(
                    model=model,
                    max_tokens=thinking_budget + 4096,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                    tools=[REPORT_FINDINGS_TOOL],
                    tool_choice={"type": "any"},
                    thinking={"type": "enabled", "budget_tokens": thinking_budget},
                    timeout=180.0,
                )
            else:
                response = await client.messages.create(
                    model=model,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                    tools=[REPORT_FINDINGS_TOOL],
                    tool_choice={"type": "any"},
                    timeout=80.0,
                )
            return response
        except anthropic.RateLimitError:
            if attempt < _MAX_RETRIES:
                delay = _RETRY_BASE_DELAY * (2.0**attempt)
                logger.warning(
                    "[retry] %s — rate limited; retrying in %.0fs (attempt %d/%d)",
                    agent_id, delay, attempt + 1, _MAX_RETRIES,
                )
                await asyncio.sleep(delay)
            else:
                raise
        except anthropic.APIStatusError as exc:
            if exc.status_code >= 500 and attempt < _MAX_RETRIES:
                delay = _RETRY_BASE_DELAY * (2.0**attempt)
                logger.warning(
                    "[retry] %s — server error %d; retrying in %.0fs (attempt %d/%d)",
                    agent_id, exc.status_code, delay, attempt + 1, _MAX_RETRIES,
                )
                await asyncio.sleep(delay)
            else:
                raise
    raise RuntimeError("unreachable")  # mypy: all paths above return or raise


# ── Agent runner ──────────────────────────────────────────────────────────────


async def call_agent(
    *,
    agent_id: str,
    agent_name: str,
    agent_icon: str,
    system_prompt: str,
    user_prompt: str,
) -> AgentResult:
    """Run a single agent via Claude tool use and return structured findings.

    Always returns an AgentResult — errors are captured in the result, not raised.
    """
    settings = get_settings()
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    result = AgentResult(
        agent_id=agent_id,
        agent_name=agent_name,
        agent_icon=agent_icon,
        status=AgentStatus.RUNNING,
    )

    findings: list[Finding] = []
    summary: str = ""

    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = await _make_api_call(
                client,
                agent_id=agent_id,
                model=settings.model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                enable_thinking=settings.enable_thinking,
                thinking_budget=settings.thinking_budget_tokens,
            )
        except anthropic.RateLimitError:
            result.status = AgentStatus.ERROR
            result.error = f"Rate limit: all {_MAX_RETRIES} retries exhausted"
            return result
        except anthropic.APIStatusError as exc:
            result.status = AgentStatus.ERROR
            result.error = f"API error ({exc.status_code}): {exc.message}"
            return result
        except anthropic.APIError as exc:
            result.status = AgentStatus.ERROR
            result.error = f"API error: {exc.message}"
            return result
        except Exception as exc:
            result.status = AgentStatus.ERROR
            result.error = f"Agent timed out or failed: {exc}"
            return result

        findings = _extract_findings(response.content, agent_id=agent_id, agent_name=agent_name)
        summary = _extract_summary(response.content)

        if findings:
            break

        if attempt < _MAX_RETRIES:
            delay = _RETRY_BASE_DELAY * (2.0**attempt)
            logger.warning(
                "[retry] %s — no tool call in response (stop_reason=%r); "
                "retrying in %.0fs (attempt %d/%d)",
                agent_id,
                getattr(response, "stop_reason", "unknown"),
                delay,
                attempt + 1,
                _MAX_RETRIES,
            )
            await asyncio.sleep(delay)

    if not findings:
        result.status = AgentStatus.ERROR
        result.error = "No structured findings returned by the model"
        return result

    result.findings = _apply_guardrails(findings, agent_id=agent_id)
    result.summary = summary
    result.thinking = _extract_thinking(response.content)
    result.status = AgentStatus.COMPLETED
    return result


def _extract_findings(
    content: list[anthropic.types.ContentBlock],
    *,
    agent_id: str,
    agent_name: str,
) -> list[Finding]:
    for block in content:
        if block.type == "tool_use" and block.name == "report_findings":
            tool_input = cast(dict[str, Any], block.input)
            raw: list[dict[str, Any]] = tool_input.get("findings", [])
            return [_parse_finding(f, agent_id=agent_id, agent_name=agent_name) for f in raw]
    return []


def _extract_summary(content: list[anthropic.types.ContentBlock]) -> str:
    for block in content:
        if block.type == "tool_use" and block.name == "report_findings":
            tool_input = cast(dict[str, Any], block.input)
            return str(tool_input.get("summary", ""))
    return ""


def _parse_finding(
    raw: dict[str, Any],
    *,
    agent_id: str,
    agent_name: str,
) -> Finding:
    return Finding(
        id=str(uuid.uuid4()),
        title=raw["title"],
        description=raw["description"],
        confidence=ConfidenceLevel(raw["confidence"]),
        confidence_score=float(raw["confidence_score"]),
        evidence=raw.get("evidence", ""),
        assumptions=raw.get("assumptions", []),
        needs_validation=raw.get("needs_validation", []),
        recommended_action=raw.get("recommended_action", ""),
        category=raw.get("category", "general"),
        agent_id=agent_id,
        agent_name=agent_name,
    )
