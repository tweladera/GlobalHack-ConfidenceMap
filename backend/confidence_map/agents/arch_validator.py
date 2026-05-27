"""Architecture Validator agent — detects drift, coupling risks, and SLA contradictions."""

from __future__ import annotations

from confidence_map.agents.base import call_agent
from confidence_map.models.findings import AgentResult

AGENT_ID = "arch_validator"
AGENT_NAME = "Architecture Validator"
AGENT_ICON = "GitBranch"

_SYSTEM = """You are the Architecture Validator agent of the Confidence Map platform.

Evaluate architectural decisions, ADRs, and service structures to detect:
- Architectural drift: implementation diverging from stated architecture
- Dangerous coupling: tight dependencies blocking independent scaling/deployment
- Scalability risks: bottlenecks that fail under load
- SLA contradictions: architecture that cannot meet stated reliability/latency targets
- Missing resilience patterns: absent retry, circuit breakers, caching, idempotency
- Single points of failure

Confidence levels:
  GREEN  = architecture explicitly addresses this concern
  YELLOW = architecture implies a solution but does not confirm it
  RED    = architecture contradicts requirements or leaves a critical gap

Reference specific components or decisions. Produce 4-7 findings.
Write your summary for both an engineer and a CTO audience."""

_USER_TEMPLATE = """Validate the following architecture against the specification:

<spec>
{spec}
</spec>

{arch_block}{ctx_block}
Identify architectural risks, contradictions, and resilience gaps."""


async def run(
    spec: str, architecture: str = "", context: str = "", language: str = "en"
) -> AgentResult:
    _no_arch = "<architecture>No architecture provided — infer from the spec.</architecture>\n\n"
    arch_block = f"<architecture>{architecture}</architecture>\n\n" if architecture else _no_arch
    ctx_block = f"<context>{context}</context>\n\n" if context else ""
    return await call_agent(
        agent_id=AGENT_ID,
        agent_name=AGENT_NAME,
        agent_icon=AGENT_ICON,
        system_prompt=_SYSTEM,
        user_prompt=_USER_TEMPLATE.format(
            spec=spec, arch_block=arch_block, ctx_block=ctx_block
        ),
        language=language,
    )
