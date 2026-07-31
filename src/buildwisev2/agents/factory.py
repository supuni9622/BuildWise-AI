"""AgentFactory — the only place native ``crewai.Agent`` instances are constructed.

Tasks and Crews must never instantiate ``Agent`` directly; they always go
through this factory so model tier resolution, tool attachment, and Skill
attachment stay centralized.
"""

from __future__ import annotations

from pathlib import Path

from crewai import Agent

from buildwisev2.agents.contracts import AgentContract, AgentType, get_contract
from buildwisev2.config.settings import Settings, get_settings
from buildwisev2.tools.registry import resolve_tools

_SKILLS_ROOT = Path(__file__).resolve().parent.parent / "skills"


def _skill_directory_name(agent_type: AgentType) -> str:
    """Convert ``AgentType.value`` (snake_case) to the kebab-case Skill directory name."""

    return agent_type.value.replace("_", "-")


class AgentFactory:
    """Builds native CrewAI Agents from static contracts + resolved settings."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def create(self, agent_type: AgentType) -> Agent:
        contract = get_contract(agent_type)
        return self._build(contract)

    def _build(self, contract: AgentContract) -> Agent:
        model = self._settings.resolve_model(contract.model_tier)
        tools = resolve_tools(contract.tool_keys) if contract.tool_keys else None
        skills = self._resolve_skills(contract.agent_type)
        return Agent(
            role=contract.role,
            goal=contract.goal,
            backstory=contract.backstory,
            llm=model,
            allow_delegation=contract.allow_delegation,
            max_iter=contract.max_iter,
            verbose=self._settings.crewai_verbose,
            cache=True,
            tools=tools,
            skills=skills,
        )

    def _resolve_skills(self, agent_type: AgentType) -> list[str] | None:
        skill_file = _SKILLS_ROOT / _skill_directory_name(agent_type) / "SKILL.md"
        if not skill_file.exists():
            return None
        # CrewAI treats a bare directory Path as a *search root* to scan for
        # skill subdirectories (crewai.skills.loader.discover_skills), which
        # would pull in every specialist's Skill for every Agent. Passing the
        # raw "---\n" frontmatter content instead loads exactly this one
        # Skill (crewai.skills.loader.load_skill's inline-string branch).
        return [skill_file.read_text(encoding="utf-8")]
