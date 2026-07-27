"""CrewAI crew definitions.

BuildWise has a fixed, four-stage business Crew topology rather than a
plugin-based Crew system, so the Flow imports these factories explicitly.
There is no Crew registry.
"""

from buildwise.crews.discovery import create_discovery_crew
from buildwise.crews.lead_review import create_lead_review_crew
from buildwise.crews.product_planning import (
    assemble_product_planning_result,
    create_product_planning_crew,
)
from buildwise.crews.technical_planning import (
    assemble_technical_planning_result,
    create_technical_planning_crew,
)

__all__ = [
    "assemble_product_planning_result",
    "assemble_technical_planning_result",
    "create_discovery_crew",
    "create_lead_review_crew",
    "create_product_planning_crew",
    "create_technical_planning_crew",
]
