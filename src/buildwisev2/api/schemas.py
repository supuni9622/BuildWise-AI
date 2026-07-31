"""API request/response schemas matching the existing ``web/`` frontend contract.

These are intentionally separate from the domain layer: the frontend's
intake shape (title, known_features, target_platforms, ...) is a UI
convenience, not a BuildWise domain concept — ``service.py`` translates
between the two.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

QuestionType = Literal[
    "free_text", "single_choice", "multiple_choice", "boolean", "integer", "decimal"
]


class IntakeRequest(BaseModel):
    title: str | None = None
    idea: str = Field(min_length=20)
    target_users: list[str] = Field(default_factory=list)
    known_features: list[str] = Field(default_factory=list)
    target_platforms: list[str] = Field(default_factory=list)
    delivery_expectation: str | None = None
    preferred_timeline: str | None = None
    estimated_budget: str | None = None
    requests_ai_capabilities: bool | None = None
    handles_sensitive_data: bool | None = None
    submission_channel: str | None = None


class QuestionSchema(BaseModel):
    id: str
    category: str
    question: str
    question_type: QuestionType
    rationale: str
    required: bool
    options: list[str] = Field(default_factory=list)
    placeholder: str | None = None
    help_text: str | None = None


class ConsultationResponse(BaseModel):
    consultation_id: str
    status: str
    stage: str
    clarification_round: int
    questions: list[QuestionSchema] = Field(default_factory=list)
    active_operation: str | None = None


class ClarificationAnswerSchema(BaseModel):
    question_id: str
    answer: str | list[str] | bool


class ClarificationSubmission(BaseModel):
    clarification_round: int
    answers: list[ClarificationAnswerSchema]


class BlueprintSectionSchema(BaseModel):
    section: str
    title: str
    summary: str
    markdown: str


class BlueprintSchema(BaseModel):
    title: str
    executive_summary: str
    sections: list[BlueprintSectionSchema]
    open_questions: list[str]
    limitations: list[str]
    generated_markdown: str
    version: str


class BlueprintResultResponse(BaseModel):
    result: BlueprintSchema
