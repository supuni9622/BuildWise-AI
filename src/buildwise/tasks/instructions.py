"""Shared prompt instruction blocks for BuildWise CrewAI tasks.

Formatting text that must stay identical across every specialist task
factory lives here instead of being duplicated (and drifting) in each
module.
"""

from __future__ import annotations

IDENTIFIER_RULES = (
    "Identifier rules:\n"
    "- Every id and every value in an *_id or *_ids reference field must "
    "be a complete RFC 4122 UUID string (for example, "
    "'6ba7b810-9dad-11d1-80b4-00c04fd430c8').\n"
    "- Do not emit descriptive labels such as 'segment-001', "
    "'competitor-001', or 'goal-001' as identifiers, and do not shorten, "
    "abbreviate, or slugify a UUID.\n"
    "- Reuse the exact generated UUID when another field references that "
    "artifact; do not generate a different UUID for the reference.\n"
    "- Never repeat an ID within the same list, and never reference an "
    "identifier that was not actually generated in this response.\n"
)
"""Every field typed as a UUID enforces that type when the draft is parsed,
but OpenAI's structured-output JSON Schema mode does not actually constrain
string *content* to UUID format server-side — only Pydantic's client-side
parsing does, after the response already exists. A field-typed ID mismatch
therefore raises before any TaskOutput exists, bypassing the guardrail
retry-with-feedback loop entirely (the same failure shape `_draft_model`
otherwise protects against). Repeating this instruction firmly in every
task that generates identifiers is the only lever available to prevent it,
since there is no way to loosen a UUID field's type without losing
cross-reference integrity."""
