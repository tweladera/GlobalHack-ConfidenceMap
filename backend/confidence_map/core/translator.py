"""Post-analysis translation: translates AgentResult findings via Claude."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

import anthropic

from confidence_map.core.settings import get_settings
from confidence_map.models.findings import AgentResult

logger = logging.getLogger(__name__)

_LANG_NAMES: dict[str, str] = {
    "en": "English",
    "es": "Spanish",
    "pt": "Brazilian Portuguese",
}


def _extract_json(text: str) -> dict[str, Any]:
    """Extract JSON from Claude response, handling optional markdown code blocks."""
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return dict(json.loads(match.group(1).strip()))
    return dict(json.loads(text.strip()))


async def _translate_agent(result: AgentResult, language: str) -> AgentResult:
    """Translate a single agent's findings and summary to the target language.

    Returns the original result unchanged if translation fails (graceful fallback).
    """
    if not result.findings:
        return result

    settings = get_settings()
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    lang_name = _LANG_NAMES.get(language, "English")

    findings_data = [
        {
            "idx": i,
            "title": f.title,
            "description": f.description,
            "evidence": f.evidence,
            "assumptions": f.assumptions,
            "needs_validation": f.needs_validation,
            "recommended_action": f.recommended_action,
        }
        for i, f in enumerate(result.findings)
    ]

    prompt = (
        f"Translate the following software analysis findings to {lang_name}.\n\n"
        "Return ONLY a JSON object with this exact structure (no markdown, no explanation):\n"
        "{\n"
        '  "summary": "<translated summary>",\n'
        '  "findings": [\n'
        "    {\n"
        '      "idx": <same integer as input>,\n'
        '      "title": "<translated>",\n'
        '      "description": "<translated>",\n'
        '      "evidence": "<translated>",\n'
        '      "assumptions": ["<translated item>"],\n'
        '      "needs_validation": ["<translated item>"],\n'
        '      "recommended_action": "<translated>"\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- Preserve technical terms, acronyms, proper nouns, and code identifiers exactly as-is.\n"
        "- Do NOT translate: confidence levels (green/yellow/red), category names, or IDs.\n"
        "- Keep the same idx values from the input.\n\n"
        f"Summary to translate:\n{result.summary}\n\n"
        f"Findings to translate:\n{json.dumps(findings_data, ensure_ascii=False, indent=2)}"
    )

    try:
        response = await client.messages.create(
            model=settings.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
            timeout=60.0,
        )
        text = next((block.text for block in response.content if hasattr(block, "text")), "")
        translated = _extract_json(text)

        translated_map: dict[int, dict[str, Any]] = {
            int(item["idx"]): item for item in translated.get("findings", [])
        }

        new_findings = []
        for i, f in enumerate(result.findings):
            t = translated_map.get(i, {})
            new_findings.append(
                f.model_copy(
                    update={
                        "title": t.get("title", f.title),
                        "description": t.get("description", f.description),
                        "evidence": t.get("evidence", f.evidence),
                        "assumptions": t.get("assumptions", f.assumptions),
                        "needs_validation": t.get("needs_validation", f.needs_validation),
                        "recommended_action": t.get("recommended_action", f.recommended_action),
                    }
                )
            )

        return result.model_copy(
            update={
                "findings": new_findings,
                "summary": translated.get("summary", result.summary),
            }
        )
    except Exception as exc:
        logger.warning("[translator] Failed to translate agent %s: %s", result.agent_id, exc)
        return result  # graceful fallback — show original language


async def translate_agent_results(agents: list[AgentResult], language: str) -> list[AgentResult]:
    """Translate all agent results to the target language in parallel."""
    return list(await asyncio.gather(*(_translate_agent(a, language) for a in agents)))
