from pydantic import BaseModel

from buildwise.observability.crewai_telemetry import (
    _provider_name,
    _schema_chars,
    _serialized_chars,
    _token_estimate,
)


class _Response(BaseModel):
    answer: str
    confidence: float


def test_schema_measurement_uses_compact_strict_json() -> None:
    size = _schema_chars(_Response)

    assert size > 0
    assert size == len(
        '{"properties":{"answer":{"title":"Answer","type":"string"},'
        '"confidence":{"title":"Confidence","type":"number"}},'
        '"required":["answer","confidence"],"title":"_Response","type":"object"}'
    )


def test_context_measurement_handles_messages_and_token_estimate() -> None:
    messages = [{"role": "user", "content": "hello"}]

    assert _serialized_chars(messages) == len('[{"role":"user","content":"hello"}]')
    assert _token_estimate(5) == 2


def test_provider_is_derived_from_crewai_model_name() -> None:
    assert _provider_name("openai/gpt-5-mini") == "openai"
    assert _provider_name("custom-model") is None
