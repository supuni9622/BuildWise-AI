"""Deterministic BuildWise specialist planning package.

This package converts validated Discovery and Product Planning signals into
a canonical ``SpecialistExecutionPlan``. It is ordinary, framework-free
Python: no CrewAI imports, no LLM calls, no database access.
"""

from __future__ import annotations

from buildwise.planning.planner import SpecialistPlanner, SpecialistPlanningError

SPECIALIST_PLANNER = SpecialistPlanner()

__all__ = [
    "SPECIALIST_PLANNER",
    "SpecialistPlanner",
    "SpecialistPlanningError",
]
