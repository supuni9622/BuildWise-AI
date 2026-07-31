"""Run the BuildWise v2 API with ``python -m buildwisev2.api``."""

from __future__ import annotations

import uvicorn

from buildwisev2.api.app import app
from buildwisev2.config.settings import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
