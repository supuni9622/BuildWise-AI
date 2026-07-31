"""In-process consultation session registry, backed by SQLite Flow persistence.

Not a database layer of its own — ``ConsultingFlow`` already checkpoints
its state to SQLite via the native ``crewai.flow.persistence`` interface
(see ``flows/consulting_flow.py``). This module just keeps a fast
in-memory index of live ``ConsultingFlow`` instances for the current
process, and falls back to loading a persisted checkpoint when a
consultation isn't in memory (e.g. after a process restart).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path

from crewai.flow.persistence import SQLiteFlowPersistence

from buildwisev2.agents.factory import AgentFactory
from buildwisev2.config.settings import Settings, get_settings
from buildwisev2.flows.consulting_flow import ConsultingFlow
from buildwisev2.flows.state import ConsultingFlowState


@dataclass
class ConsultationSession:
    """Bookkeeping for one live or restored consultation."""

    consultation_id: str
    flow: ConsultingFlow
    lock: threading.Lock = field(default_factory=threading.Lock)
    thread: threading.Thread | None = None
    error: str | None = None
    pending_questions: dict[str, str] = field(default_factory=dict)
    """question id -> question text, populated while awaiting clarification."""


class ConsultationStore:
    """Process-wide registry of consultation sessions.

    Restoring after a restart hydrates ``ConsultingFlowState`` from the
    SQLite checkpoint, but does not re-enter the Flow graph — the session
    becomes readable immediately (status, and the blueprint if it had
    completed) and resumes forward progress only when the caller submits
    clarification answers or the consultation is otherwise re-kicked off.
    See ``PROGRESS.md`` for the exact resume contract.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._sessions: dict[str, ConsultationSession] = {}
        self._index_lock = threading.Lock()
        Path(self._settings.flow_persistence_db_path).parent.mkdir(parents=True, exist_ok=True)
        self._persistence = SQLiteFlowPersistence(self._settings.flow_persistence_db_path)

    @property
    def persistence(self) -> SQLiteFlowPersistence:
        return self._persistence

    def new_flow(self, agent_factory: AgentFactory | None = None) -> ConsultingFlow:
        """Construct a fresh, persistence-backed ``ConsultingFlow``."""

        return ConsultingFlow(
            agent_factory=agent_factory,
            settings=self._settings,
            persistence=self._persistence,
        )

    def register(self, session: ConsultationSession) -> None:
        with self._index_lock:
            self._sessions[session.consultation_id] = session

    def get(self, consultation_id: str) -> ConsultationSession | None:
        with self._index_lock:
            session = self._sessions.get(consultation_id)
        if session is not None:
            return session
        return self._restore(consultation_id)

    def _restore(self, consultation_id: str) -> ConsultationSession | None:
        stored_state = self._persistence.load_state(consultation_id)
        if not stored_state:
            return None

        flow = self.new_flow()
        # ``Flow.state`` has no public setter; CrewAI only exposes the
        # private backing attribute for direct hydration outside of kickoff().
        flow._state = ConsultingFlowState.model_validate(stored_state)
        session = ConsultationSession(consultation_id=consultation_id, flow=flow)
        self.register(session)
        return session


STORE = ConsultationStore()
