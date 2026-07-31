"""Intake domain models: the raw product idea and clarification exchange."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from buildwisev2.domain.common import BuildWiseModel


class ProductIdeaRequest(BuildWiseModel):
    """The user-submitted product idea that starts a consultation."""

    session_id: UUID
    title: str | None = None
    raw_idea: str
    target_users: str | None = None
    known_constraints: list[str] = Field(default_factory=list)
    explicitly_requested_specialists: list[str] = Field(default_factory=list)
    explicitly_excluded_specialists: list[str] = Field(default_factory=list)


class ClarificationAnswer(BuildWiseModel):
    """One structured answer to a Discovery clarification question."""

    question: str
    answer: str


class ProductIdeaContext(BuildWiseModel):
    """Accumulated clarification context for a session, supplied back to Discovery."""

    session_id: UUID
    clarification_answers: list[ClarificationAnswer] = Field(default_factory=list)
    clarification_round: int = 0
