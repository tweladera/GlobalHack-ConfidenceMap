"""Base agent: Claude tool-use call that returns structured findings."""

from __future__ import annotations

import uuid
from typing import Any, cast

import anthropic

from confidence_map.core.settings import get_settings
from confidence_map.models.findings import AgentResult, AgentStatus, ConfidenceLevel, Finding

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
            "description": "0.0=maximum uncertainty, 1.0=fully confirmed",
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


# ── Language instructions ──────────────────────────────────────────────────────

_LANG_INSTRUCTIONS: dict[str, str] = {
    "en": "",
    "es": (
        "\n\nIMPORTANT: Respond entirely in Spanish. All finding titles, descriptions, "
        "evidence, assumptions, validation items, recommended actions, and the summary "
        "must be written in Spanish."
    ),
    "pt": (
        "\n\nIMPORTANT: Respond entirely in Brazilian Portuguese. All finding titles, "
        "descriptions, evidence, assumptions, validation items, recommended actions, "
        "and the summary must be written in Brazilian Portuguese."
    ),
}


# ── Agent runner ──────────────────────────────────────────────────────────────


async def call_agent(
    *,
    agent_id: str,
    agent_name: str,
    agent_icon: str,
    system_prompt: str,
    user_prompt: str,
    language: str = "en",
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

    lang_instruction = _LANG_INSTRUCTIONS.get(language, "")
    try:
        response = await client.messages.create(
            model=settings.model,
            max_tokens=2048,
            system=system_prompt + lang_instruction,
            messages=[{"role": "user", "content": user_prompt}],
            tools=[REPORT_FINDINGS_TOOL],
            tool_choice={"type": "any"},
            timeout=90.0,
        )
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

    if not findings:
        result.status = AgentStatus.ERROR
        result.error = "No structured findings returned by the model"
        return result

    result.findings = findings
    result.summary = summary
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
