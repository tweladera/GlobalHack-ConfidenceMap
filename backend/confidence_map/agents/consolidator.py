"""Consolidator agent — cross-agent audit: contradictions, confirmed criticals, redundancies."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, cast

import anthropic

from confidence_map.core.settings import get_settings
from confidence_map.models.findings import (
    AgentResult,
    ConfirmedCritical,
    ConsolidatorResult,
    Contradiction,
    Redundancy,
)

logger = logging.getLogger(__name__)

AGENT_ID = "consolidator"
AGENT_NAME = "Consolidator"
AGENT_ICON = "GitMerge"

_MAX_RETRIES = 2
_RETRY_BASE_DELAY = 2.0

# ── Tool schema ────────────────────────────────────────────────────────────────

_CONSOLIDATION_TOOL: anthropic.types.ToolParam = {
    "name": "report_consolidation",
    "description": (
        "Report the cross-agent audit: contradictions, confirmed criticals, redundancies"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "contradictions": {
                "type": "array",
                "description": (
                    "Findings where two agents assign conflicting confidence levels"
                    " to the same topic"
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Short label for the conflict"},
                        "agents": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "agent_ids of the conflicting agents",
                        },
                        "description": {
                            "type": "string",
                            "description": "What each agent claimed and why they conflict",
                        },
                        "resolution": {
                            "type": "string",
                            "description": "Which finding is more accurate and why",
                        },
                    },
                    "required": ["topic", "agents", "description", "resolution"],
                },
            },
            "confirmed_criticals": {
                "type": "array",
                "description": (
                    "RED findings independently flagged by two or more agents - highest priority"
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"},
                        "agents": {"type": "array", "items": {"type": "string"}},
                        "combined_evidence": {
                            "type": "string",
                            "description": (
                                "Merged evidence from all agents that agree on this risk"
                            ),
                        },
                    },
                    "required": ["topic", "agents", "combined_evidence"],
                },
            },
            "redundancies": {
                "type": "array",
                "description": "Findings covering the same concern from different agents",
                "items": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"},
                        "agents": {"type": "array", "items": {"type": "string"}},
                        "kept": {
                            "type": "string",
                            "description": "agent_id of the most complete finding to surface",
                        },
                    },
                    "required": ["topic", "agents", "kept"],
                },
            },
            "audit_summary": {
                "type": "string",
                "description": (
                    "One paragraph: overall audit verdict, most critical action items, "
                    "and confidence in the combined analysis."
                ),
            },
        },
        "required": ["contradictions", "confirmed_criticals", "redundancies", "audit_summary"],
    },
}

_SYSTEM = """You are the Consolidator — the final audit layer of the Confidence Map platform.

Your role is to cross-examine all findings produced by the six specialist agents and act as
an impartial Editor-in-Chief. You do NOT repeat or summarise individual findings. Instead:

1. CONTRADICTIONS: Identify topics where two agents assign conflicting confidence levels
   (e.g., Arch Validator says GREEN; Risk Intelligence says RED for the same concern).
   Determine which is more accurate and explain why.

2. CONFIRMED CRITICALS: Find RED findings independently raised by two or more agents —
   these represent the highest-confidence risks and should be escalated immediately.

3. REDUNDANCIES: Flag findings that cover the same concern across agents and identify
   which version is most complete (to avoid noise in the final report).

4. AUDIT SUMMARY: Conclude with a one-paragraph verdict for the delivery team, naming
   the top 2-3 actions they must take before proceeding.

Be precise. Reference agent names and finding titles. Do not be lenient — your job is
to sharpen the signal, not soften it."""

_USER_TEMPLATE = """Review the following findings from all six specialist agents and produce
the cross-agent audit:

{findings_block}

Apply the consolidation criteria: contradictions, confirmed criticals, redundancies, and
produce a final audit summary."""


# ── Helpers ────────────────────────────────────────────────────────────────────


def _format_all_findings(agent_results: list[AgentResult]) -> str:
    """Render all agent findings as a compact, structured block for the Consolidator prompt."""
    lines: list[str] = []
    for result in agent_results:
        if result.error or not result.findings:
            continue
        lines.append(f"=== {result.agent_name.upper()} ===")
        for f in result.findings:
            score_pct = round(f.confidence_score * 100)
            lines.append(f"  [{f.confidence.upper()} | {score_pct}%] {f.title}")
            suffix = "..." if len(f.evidence) > 200 else ""
            lines.append(f"    Evidence: {f.evidence[:200].rstrip()}{suffix}")
        lines.append("")
    return "\n".join(lines)


def _parse_consolidation(tool_input: dict[str, Any]) -> ConsolidatorResult:
    """Parse the Consolidator tool output into a ConsolidatorResult."""
    contradictions = [
        Contradiction(**item) for item in tool_input.get("contradictions", [])
    ]
    confirmed_criticals = [
        ConfirmedCritical(**item) for item in tool_input.get("confirmed_criticals", [])
    ]
    redundancies = [
        Redundancy(**item) for item in tool_input.get("redundancies", [])
    ]
    return ConsolidatorResult(
        contradictions=contradictions,
        confirmed_criticals=confirmed_criticals,
        redundancies=redundancies,
        audit_summary=tool_input.get("audit_summary", ""),
    )


# ── Agent runner ───────────────────────────────────────────────────────────────


async def run(agent_results: list[AgentResult]) -> ConsolidatorResult:
    """Run the Consolidator over all agent results and return a structured audit.

    Returns an empty ConsolidatorResult (with a warning summary) on failure
    so the pipeline never breaks due to consolidation errors.
    """
    settings = get_settings()
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    findings_block = _format_all_findings(agent_results)
    if not findings_block.strip():
        logger.warning("[consolidator] No findings available to consolidate.")
        return ConsolidatorResult(audit_summary="No findings available to consolidate.")

    user_prompt = _USER_TEMPLATE.format(findings_block=findings_block)

    response = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = await client.messages.create(
                model=settings.model,
                max_tokens=4096,
                system=_SYSTEM,
                messages=[{"role": "user", "content": user_prompt}],
                tools=[_CONSOLIDATION_TOOL],
                tool_choice={"type": "any"},
                timeout=120.0,
            )
            break
        except anthropic.RateLimitError:
            if attempt < _MAX_RETRIES:
                delay = _RETRY_BASE_DELAY * (2.0**attempt)
                logger.warning(
                    "[consolidator] Rate limited; retrying in %.0fs (attempt %d/%d)",
                    delay, attempt + 1, _MAX_RETRIES,
                )
                await asyncio.sleep(delay)
            else:
                logger.warning("[consolidator] Rate limit: all retries exhausted.")
                return ConsolidatorResult(
                    audit_summary="Consolidation unavailable: rate limit exhausted."
                )
        except anthropic.APIStatusError as exc:
            if exc.status_code >= 500 and attempt < _MAX_RETRIES:
                delay = _RETRY_BASE_DELAY * (2.0**attempt)
                logger.warning(
                    "[consolidator] Server error %d; retrying in %.0fs (attempt %d/%d)",
                    exc.status_code, delay, attempt + 1, _MAX_RETRIES,
                )
                await asyncio.sleep(delay)
            else:
                logger.warning("[consolidator] API error %d: %s", exc.status_code, exc)
                return ConsolidatorResult(audit_summary=f"Consolidation unavailable: {exc}")
        except Exception as exc:
            logger.warning("[consolidator] API call failed: %s — returning empty result.", exc)
            return ConsolidatorResult(audit_summary=f"Consolidation unavailable: {exc}")

    if response is None:
        return ConsolidatorResult(audit_summary="Consolidation unavailable: no response received.")

    for block in response.content:
        if block.type == "tool_use" and block.name == "report_consolidation":
            tool_input = cast(dict[str, Any], block.input)
            try:
                return _parse_consolidation(tool_input)
            except Exception as exc:
                logger.warning("[consolidator] Failed to parse output: %s", exc)
                return ConsolidatorResult(audit_summary="Consolidation parse error.")

    logger.warning("[consolidator] No tool_use block in response.")
    return ConsolidatorResult(audit_summary="Consolidation returned no structured output.")
