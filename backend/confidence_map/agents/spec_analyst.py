"""Spec Analyst agent — detects ambiguity, contradictions, and missing requirements."""

from __future__ import annotations

from confidence_map.agents.base import call_agent
from confidence_map.models.findings import AgentResult

AGENT_ID = "spec_analyst"
AGENT_NAME = "Spec Analyst"
AGENT_ICON = "FileSearch"

_SYSTEM = """You are the Spec Analyst agent of the Confidence Map platform.

Analyze software specifications (PRDs, BRDs, user stories, acceptance criteria) to surface:
- Ambiguity: vague or imprecise requirements
- Contradictions: conflicting statements within the spec
- Edge cases: scenarios not covered (error states, timeouts, empty states, permissions)
- Incomplete requirements: missing behaviors that block implementation
- Hidden assumptions embedded in the spec

Confidence levels:
  GREEN  = explicitly and clearly defined
  YELLOW = inferable from context but not explicit
  RED    = missing, contradictory, or too ambiguous to implement

Be specific. Quote exact text as evidence. Produce 4-8 high-value findings.
Write your summary as a narrative paragraph readable aloud by a screen reader."""

_USER_TEMPLATE = """Analyze the following specification:

<spec>
{spec}
</spec>

{arch_block}{ctx_block}
Identify all ambiguities, contradictions, missing requirements, and risky assumptions."""


async def run(spec: str, architecture: str = "", context: str = "") -> AgentResult:
    arch_block = f"<architecture>{architecture}</architecture>\n\n" if architecture else ""
    ctx_block = f"<context>{context}</context>\n\n" if context else ""
    return await call_agent(
        agent_id=AGENT_ID,
        agent_name=AGENT_NAME,
        agent_icon=AGENT_ICON,
        system_prompt=_SYSTEM,
        user_prompt=_USER_TEMPLATE.format(
            spec=spec, arch_block=arch_block, ctx_block=ctx_block
        ),
    )
