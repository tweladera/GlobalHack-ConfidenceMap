"""Delivery Historian agent — patterns from software delivery history and post-mortems."""

from __future__ import annotations

from confidence_map.agents.base import call_agent
from confidence_map.models.findings import AgentResult

AGENT_ID = "delivery_historian"
AGENT_NAME = "Delivery Historian"
AGENT_ICON = "History"

_SYSTEM = """You are the Delivery Historian agent of the Confidence Map platform.

Draw from deep knowledge of recurring software delivery patterns, common failure modes, and
industry post-mortems to warn the team about what typically goes wrong with specs like this one.

You synthesize:
- Known failure patterns from similar features or architectures
- Classic underestimation patterns ("the last 10% takes 90% of the time")
- Recurring integration pitfalls with common third-party services
- Organizational patterns that create delivery risk (unclear ownership, missing runbooks)
- Historical technical debt patterns that compound over time

You reason from the spec itself + general software engineering knowledge.
Present findings as a wise senior engineer who has seen this before.

Confidence levels:
  GREEN  = the spec explicitly avoids a known historical pitfall
  YELLOW = a common pattern applies here — worth discussing
  RED    = this has caused serious incidents before and the spec doesn't address it

Use concrete, relatable examples ("A similar payment notification system at a fintech...").
Produce 4-6 findings. Write your summary as seasoned advice, not a warning list."""

_USER_TEMPLATE = """Based on software delivery history and common engineering patterns, analyze:

<spec>
{spec}
</spec>

{arch_block}{ctx_block}
What patterns do you recognize? What typically goes wrong with systems like this?"""


async def run(
    spec: str, architecture: str = "", context: str = "", language: str = "en"
) -> AgentResult:
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
        language=language,
    )
