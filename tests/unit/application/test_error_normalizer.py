from buildwise.application.error_normalizer import normalize_session_error
from buildwise.domain.enums import SessionStage
from buildwise.domain.exceptions import CrewExecutionError
from buildwise.tools.sanitizer import ToolExecutionError


def test_crew_execution_error_is_distinguishable_and_marked_retryable() -> None:
    error = normalize_session_error(
        CrewExecutionError(stage="product_planning"),
        stage=SessionStage.PRODUCT_DEFINITION,
    )

    assert error.code == "crew_execution_failed"
    assert error.retryable is True
    assert error.details == {"crew_stage": "product_planning"}


def test_unknown_error_does_not_expose_raw_exception_text() -> None:
    error = normalize_session_error(
        RuntimeError("password=do-not-persist"),
        stage=SessionStage.DISCOVERY,
    )

    assert error.code == "background_execution_failed"
    assert "do-not-persist" not in error.message


def test_tool_error_preserves_safe_category_only() -> None:
    error = normalize_session_error(
        ToolExecutionError("web_search", "timeout"),
        stage=SessionStage.DISCOVERY,
    )

    assert error.code == "tool_execution_failed"
    assert error.retryable is True
    assert error.details == {"category": "timeout"}
