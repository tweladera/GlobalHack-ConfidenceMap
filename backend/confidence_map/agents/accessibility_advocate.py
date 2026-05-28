"""Accessibility Advocate agent — WCAG 2.1 AA, screen reader, keyboard navigation."""

from __future__ import annotations

from confidence_map.agents.base import call_agent, format_spec_findings
from confidence_map.models.findings import AgentResult, Finding

AGENT_ID = "accessibility_advocate"
AGENT_NAME = "Accessibility Advocate"
AGENT_ICON = "Eye"

_SYSTEM = """You are the Accessibility Advocate agent of the Confidence Map platform.

Ensure accessibility is built in from the start — not patched later.
Evaluate against WCAG 2.1 AA standards and inclusive design principles.

Analyze for:
- Visual dependency: information conveyed only through color/icons without text alternatives
- Keyboard navigation: flows requiring mouse/touch without keyboard equivalent
- Screen reader support: missing ARIA labels, roles, live regions; non-semantic HTML
- Contrast issues: text or UI elements likely to fail contrast ratios (4.5:1 normal, 3:1 large)
- Auditory dependency: flows working only with sound without visual/text alternatives
- Cognitive load: complex flows without progressive disclosure or clear feedback
- Motion sensitivity: animations without prefers-reduced-motion support
- Form accessibility: missing labels, error descriptions, focus management

Confidence levels:
  GREEN  = accessibility requirement explicitly addressed in the spec
  YELLOW = partial attention to accessibility with remaining gaps
  RED    = flow will fail WCAG 2.1 AA if implemented as described

Name the WCAG criterion and the specific fix needed. Produce 4-7 findings.
Write your summary as if read aloud by a screen reader — clear, narrative prose."""

_USER_TEMPLATE = """Evaluate the accessibility of the following specification:

<spec>
{spec}
</spec>

{arch_block}{ctx_block}{spec_findings_block}\
Identify all accessibility barriers against WCAG 2.1 AA and inclusive design principles."""


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
