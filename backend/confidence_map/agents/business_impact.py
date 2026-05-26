"""Business Impact agent — cost, velocity, UX degradation, and compliance risk."""

from __future__ import annotations

from confidence_map.agents.base import call_agent
from confidence_map.models.findings import AgentResult

AGENT_ID = "business_impact"
AGENT_NAME = "Business Impact"
AGENT_ICON = "TrendingUp"

_SYSTEM = """You are the Business Impact agent of the Confidence Map platform.

Connect engineering decisions to business outcomes and surface hidden costs:
- Cloud cost impact: architectural choices that multiply infrastructure costs at scale
- Operational cost: manual processes, support burden, on-call escalation risk
- Delivery delay risk: technical decisions that slow velocity or block release
- UX degradation: performance or reliability choices that degrade user experience
- Revenue/compliance risk: SLA violations, regulatory exposure, contractual obligations
- Opportunity cost: technical debt that delays future features

Confidence levels:
  GREEN  = business impact explicitly quantified or bounded in the spec
  YELLOW = impact is real but magnitude is inferred from context
  RED    = impact is unknown or potentially severe with no defined bound

Be specific about the business consequence. Produce 4-6 findings.
Write your summary for a CTO or product leader audience."""

_USER_TEMPLATE = """Analyze the business impact of the following specification:

<spec>
{spec}
</spec>

{arch_block}{ctx_block}
Focus on cost, delivery velocity, UX, compliance, and unbounded business risk."""


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
