"""Application-level telemetry for native CrewAI LLM calls.

CrewAI's aggregate usage metrics are useful for budgeting, but they do not
identify which provider call consumed the time or how large that call was.
This listener converts CrewAI's native event stream into correlated,
structured log records without adding another callback to the provider path.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from typing import Any

import structlog
from crewai import Crew
from crewai.events.base_event_listener import BaseEventListener
from crewai.events.event_bus import CrewAIEventsBus
from crewai.events.types.llm_events import (
    LLMCallCompletedEvent,
    LLMCallFailedEvent,
    LLMCallStartedEvent,
)
from crewai.events.types.task_events import (
    TaskCompletedEvent,
    TaskFailedEvent,
    TaskStartedEvent,
)
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class _TaskContext:
    consultation_id: str
    flow_id: str
    crew_id: str
    crew_name: str
    stage: str
    task_id: str
    task_name: str
    agent_id: str | None
    agent_role: str | None
    response_schema_name: str | None
    response_schema_chars: int
    response_schema_token_estimate: int
    provider_retry_limit: int
    guardrail_retry_limit: int


@dataclass(frozen=True, slots=True)
class _CallStart:
    timestamp: datetime
    context: _TaskContext | None
    iteration: int
    input_chars: int
    input_token_estimate: int
    tools_schema_chars: int


@dataclass(frozen=True, slots=True)
class _TaskStart:
    timestamp: datetime
    attempt: int


class CrewAILatencyTelemetry(BaseEventListener):
    """Emit one structured latency record for each LLM and task execution."""

    _instance: CrewAILatencyTelemetry | None = None
    _initialized = False

    def __new__(cls) -> CrewAILatencyTelemetry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._lock = Lock()
        self._tasks: dict[str, _TaskContext] = {}
        self._calls: dict[str, _CallStart] = {}
        self._iterations: defaultdict[str, int] = defaultdict(int)
        self._task_starts: dict[str, _TaskStart] = {}
        self._task_attempts: defaultdict[str, int] = defaultdict(int)
        super().__init__()
        self._initialized = True

    def register_crew_execution(
        self,
        crew: Crew,
        *,
        consultation_id: str,
        flow_id: str,
        stage: str,
        provider_retry_limit: int,
    ) -> None:
        """Associate CrewAI task IDs with BuildWise Flow correlation fields."""

        crew_id = str(getattr(crew, "id", crew.__class__.__name__))
        crew_name = getattr(crew, "name", None) or crew.__class__.__name__
        contexts: dict[str, _TaskContext] = {}
        for task in getattr(crew, "tasks", []):
            task_id = str(task.id)
            output_model = getattr(task, "output_pydantic", None)
            schema_chars = _schema_chars(output_model)
            agent = getattr(task, "agent", None)
            contexts[task_id] = _TaskContext(
                consultation_id=consultation_id,
                flow_id=flow_id,
                crew_id=crew_id,
                crew_name=crew_name,
                stage=stage,
                task_id=task_id,
                task_name=task.name or task.description,
                agent_id=str(agent.id) if agent is not None else None,
                agent_role=getattr(agent, "role", None),
                response_schema_name=(
                    output_model.__name__
                    if isinstance(output_model, type) and issubclass(output_model, BaseModel)
                    else None
                ),
                response_schema_chars=schema_chars,
                response_schema_token_estimate=_token_estimate(schema_chars),
                provider_retry_limit=provider_retry_limit,
                guardrail_retry_limit=getattr(task, "guardrail_max_retries", 0),
            )
        with self._lock:
            self._tasks.update(contexts)

    def setup_listeners(self, event_bus: CrewAIEventsBus) -> None:
        @event_bus.on(LLMCallStartedEvent)
        def on_llm_started(_: Any, event: LLMCallStartedEvent) -> None:
            input_chars = _serialized_chars(event.messages)
            tools_chars = _serialized_chars(event.tools)
            task_key = event.task_id or event.agent_id or event.call_id
            with self._lock:
                self._iterations[task_key] += 1
                iteration = self._iterations[task_key]
                context = self._tasks.get(event.task_id or "")
                self._calls[event.call_id] = _CallStart(
                    timestamp=event.timestamp,
                    context=context,
                    iteration=iteration,
                    input_chars=input_chars,
                    input_token_estimate=_token_estimate(input_chars),
                    tools_schema_chars=tools_chars,
                )
            logger.info(
                "llm_call_started",
                **_call_fields(event, self._calls[event.call_id]),
                request_started_at=event.timestamp.isoformat(),
            )

        @event_bus.on(LLMCallCompletedEvent)
        def on_llm_completed(_: Any, event: LLMCallCompletedEvent) -> None:
            start = self._pop_call(event.call_id)
            usage = event.usage or {}
            logger.info(
                "llm_call_completed",
                **_call_fields(event, start),
                request_completed_at=event.timestamp.isoformat(),
                duration_ms=_duration_ms(start.timestamp, event.timestamp),
                output_chars=_serialized_chars(event.response),
                input_tokens=_integer(usage, "prompt_tokens"),
                cached_input_tokens=_integer(
                    usage,
                    "cached_prompt_tokens",
                    "cache_read_input_tokens",
                ),
                output_tokens=_integer(usage, "completion_tokens"),
                reasoning_tokens=_integer(usage, "reasoning_tokens"),
                total_tokens=_integer(usage, "total_tokens"),
                finish_reason=event.finish_reason,
                provider_response_id=event.response_id,
            )

        @event_bus.on(LLMCallFailedEvent)
        def on_llm_failed(_: Any, event: LLMCallFailedEvent) -> None:
            start = self._pop_call(event.call_id)
            logger.error(
                "llm_call_failed",
                **_call_fields(event, start),
                request_failed_at=event.timestamp.isoformat(),
                duration_ms=_duration_ms(start.timestamp, event.timestamp),
                error_category=type(event).__name__,
                error=event.error,
            )

        @event_bus.on(TaskStartedEvent)
        def on_task_started(_: Any, event: TaskStartedEvent) -> None:
            task_id = event.task_id or ""
            with self._lock:
                self._task_attempts[task_id] += 1
                attempt = self._task_attempts[task_id]
                self._task_starts[task_id] = _TaskStart(event.timestamp, attempt)

        @event_bus.on(TaskCompletedEvent)
        def on_task_completed(_: Any, event: TaskCompletedEvent) -> None:
            self._log_task_end(event, failed=False)

        @event_bus.on(TaskFailedEvent)
        def on_task_failed(_: Any, event: TaskFailedEvent) -> None:
            self._log_task_end(event, failed=True)

    def _pop_call(self, call_id: str) -> _CallStart:
        with self._lock:
            return self._calls.pop(
                call_id,
                _CallStart(
                    timestamp=datetime.now().astimezone(),
                    context=None,
                    iteration=1,
                    input_chars=0,
                    input_token_estimate=0,
                    tools_schema_chars=0,
                ),
            )

    def _log_task_end(
        self,
        event: TaskCompletedEvent | TaskFailedEvent,
        *,
        failed: bool,
    ) -> None:
        task_id = event.task_id or ""
        with self._lock:
            start = self._task_starts.pop(task_id, None)
            context = self._tasks.get(task_id)
        fields = _context_fields(context)
        fields.update(
            task_id=task_id or None,
            task_name=event.task_name,
            guardrail_attempt=start.attempt if start is not None else None,
            validation_duration_ms=(
                _duration_ms(start.timestamp, event.timestamp) if start is not None else None
            ),
            error_category=type(event).__name__ if failed else None,
        )
        log = logger.error if failed else logger.info
        log("task_validation_failed" if failed else "task_validation_completed", **fields)


def register_crew_telemetry(
    crew: Crew,
    *,
    consultation_id: str,
    flow_id: str,
    stage: str,
    provider_retry_limit: int,
) -> None:
    """Register a Crew execution with the process-wide telemetry listener."""

    CREWAI_LATENCY_TELEMETRY.register_crew_execution(
        crew,
        consultation_id=consultation_id,
        flow_id=flow_id,
        stage=stage,
        provider_retry_limit=provider_retry_limit,
    )


def _call_fields(
    event: LLMCallStartedEvent | LLMCallCompletedEvent | LLMCallFailedEvent,
    start: _CallStart,
) -> dict[str, Any]:
    context = start.context
    fields = _context_fields(context)
    fields.update(
        llm_call_id=event.call_id,
        task_id=event.task_id or (context.task_id if context else None),
        task_name=event.task_name or (context.task_name if context else None),
        agent_id=event.agent_id or (context.agent_id if context else None),
        agent_role=event.agent_role or (context.agent_role if context else None),
        model=event.model,
        provider=_provider_name(event.model),
        agent_iteration=start.iteration,
        input_chars=start.input_chars,
        input_token_estimate=start.input_token_estimate,
        tools_schema_chars=start.tools_schema_chars,
    )
    return fields


def _context_fields(context: _TaskContext | None) -> dict[str, Any]:
    if context is None:
        return {}
    return {
        "consultation_id": context.consultation_id,
        "flow_id": context.flow_id,
        "crew_id": context.crew_id,
        "crew_name": context.crew_name,
        "stage": context.stage,
        "response_schema_name": context.response_schema_name,
        "response_schema_chars": context.response_schema_chars,
        "response_schema_token_estimate": context.response_schema_token_estimate,
        "provider_retry_limit": context.provider_retry_limit,
        "guardrail_retry_limit": context.guardrail_retry_limit,
    }


def _schema_chars(model: Any) -> int:
    if not isinstance(model, type) or not issubclass(model, BaseModel):
        return 0
    return len(
        json.dumps(
            model.model_json_schema(mode="serialization"),
            separators=(",", ":"),
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def _serialized_chars(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, str):
        return len(value)
    try:
        return len(json.dumps(value, separators=(",", ":"), ensure_ascii=False, default=str))
    except (TypeError, ValueError):
        return len(str(value))


def _token_estimate(characters: int) -> int:
    return (characters + 3) // 4


def _duration_ms(start: datetime, end: datetime) -> int:
    return max(round((end - start).total_seconds() * 1000), 0)


def _integer(values: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = values.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return None


def _provider_name(model: str | None) -> str | None:
    if not model or "/" not in model:
        return None
    return model.split("/", maxsplit=1)[0]


CREWAI_LATENCY_TELEMETRY = CrewAILatencyTelemetry()
