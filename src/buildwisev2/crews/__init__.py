"""BuildWise v2 Crews — four focused business Crews, per ``04_crews_refactor_plan.md``.

No Crew registry is provided by design: the Flow imports these factories
explicitly, since BuildWise has a fixed business workflow rather than a
plugin-based Crew system.
"""

from buildwisev2.crews.discovery import build_discovery_kickoff_inputs, create_discovery_crew
from buildwisev2.crews.lead_review import build_lead_review_kickoff_inputs, create_lead_review_crew
from buildwisev2.crews.product_planning import (
    build_product_planning_kickoff_inputs,
    create_product_planning_crew,
)
from buildwisev2.crews.technical_planning import (
    build_technical_planning_kickoff_inputs,
    create_technical_planning_crew,
)

__all__ = [
    "build_discovery_kickoff_inputs",
    "build_lead_review_kickoff_inputs",
    "build_product_planning_kickoff_inputs",
    "build_technical_planning_kickoff_inputs",
    "create_discovery_crew",
    "create_lead_review_crew",
    "create_product_planning_crew",
    "create_technical_planning_crew",
]
