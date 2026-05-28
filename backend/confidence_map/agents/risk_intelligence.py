"""Risk Intelligence agent — security, delivery, observability, and operational risks."""

from __future__ import annotations

from confidence_map.agents.base import call_agent, format_spec_findings
from confidence_map.models.findings import AgentResult, Finding

AGENT_ID = "risk_intelligence"
AGENT_NAME = "Risk Intelligence"
AGENT_ICON = "Shield"

_SYSTEM = """You are the Risk Intelligence agent of the Confidence Map platform.

Identify delivery, security, and operational risks hidden in the specification:
- Security gaps: auth, authorization, injection, data exposure, secrets management
- Delivery risks: unrealistic scope, underdefined requirements causing creep
- Observability gaps: missing logging, metrics, tracing, alerting
- Operational risks: deployment complexity, rollback strategy, data migration risk
- Single points of failure in the proposed flow
- Dependency risk: external services without fallback or timeout strategy

Confidence levels:
  GREEN  = risk is explicitly addressed with defined mitigation
  YELLOW = risk exists with partial mitigation implied
  RED    = risk present with no mitigation — high impact if triggered

Name the exact risk, not just the category. Produce 4-8 findings.
Write your summary for both an engineer and a delivery manager."""

_USER_TEMPLATE = """Identify all risks in the following specification:

<spec>
{spec}
</spec>

{arch_block}{ctx_block}{spec_findings_block}\
Focus on security, delivery risk, observability, and operational failure modes."""


async def run(
    spec: str,
    architecture: str = "",
    context: str = "",
    spec_findings: list[Finding] | None = None,
) -> AgentResult:
    arch_block = f"<architecture>{architecture}</architecture>\n\n" if architecture else ""
    ctx_block = f"<context>{context}</context>\n\n" if context else ""
    spec_findings_block = format_spec_findings(spec_findings) if spec_findings else ""
    return await call_agent(
        agent_id=AGENT_ID,
        agent_name=AGENT_NAME,
        agent_icon=AGENT_ICON,
        system_prompt=_SYSTEM,
        user_prompt=_USER_TEMPLATE.format(
            spec=spec,
            arch_block=arch_block,
            ctx_block=ctx_block,
            spec_findings_block=spec_findings_block,
        ),
    )
