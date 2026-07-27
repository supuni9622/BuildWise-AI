from typing import cast

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel


class SmokeFlowState(BaseModel):
    message: str = ""
    completed: bool = False


class BuildWiseSmokeFlow(Flow[SmokeFlowState]):
    @start()
    def initialize(self) -> str:
        self.state.message = "BuildWise CrewAI smoke flow"
        return cast(str, self.state.message)

    @listen(initialize)
    def complete(self, message: str) -> str:
        self.state.completed = True
        return f"{message} completed."


def main() -> None:
    result = BuildWiseSmokeFlow().kickoff()
    print(result)


if __name__ == "__main__":
    main()
