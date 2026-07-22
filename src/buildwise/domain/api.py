from pydantic import BaseModel, ConfigDict


class ApiRootResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    version: str
    api_version: str
    status: str
