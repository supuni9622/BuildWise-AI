from pydantic import BaseModel, ConfigDict, Field

from buildwise.domain.blueprint import ProductBlueprint
from buildwise.domain.discovery import ClarificationQuestion
from buildwise.domain.enums import SessionStage, SessionStatus
from buildwise.domain.intake import ClarificationAnswer, ProductIdeaRequest


class ApiRootResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    version: str
    api_version: str
    status: str


class StartConsultationRequest(ProductIdeaRequest):
    """Public intake payload for starting a consultation."""


class SubmitClarificationsRequest(BaseModel):
    """Answers for the currently active clarification round."""

    model_config = ConfigDict(extra="forbid")

    clarification_round: int = Field(ge=1)
    answers: list[ClarificationAnswer] = Field(min_length=1)


class ConsultationResponse(BaseModel):
    """Current externally visible consultation lifecycle state."""

    model_config = ConfigDict(extra="forbid")

    consultation_id: str
    status: SessionStatus
    stage: SessionStage
    clarification_round: int = Field(ge=0)
    questions: list[ClarificationQuestion] = Field(default_factory=list)


class ConsultationResultResponse(BaseModel):
    """Terminal product blueprint for a completed consultation."""

    model_config = ConfigDict(extra="forbid")

    consultation_id: str
    status: SessionStatus
    stage: SessionStage
    result: ProductBlueprint
