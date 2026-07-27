import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from buildwise.api.rate_limiter import (
    ConsultationRateLimitMiddleware,
    InMemoryRateLimiter,
)
from buildwise.domain.exceptions import RateLimitExceeded


def test_rate_limiter_rejects_requests_above_capacity() -> None:
    limiter = InMemoryRateLimiter(requests=2, window_seconds=60)

    limiter.require_capacity("client:start")
    limiter.require_capacity("client:start")

    with pytest.raises(RateLimitExceeded):
        limiter.require_capacity("client:start")


def test_rate_limit_middleware_returns_normalized_429() -> None:
    app = FastAPI()
    app.add_middleware(
        ConsultationRateLimitMiddleware,
        requests=1,
        window_seconds=60,
    )

    @app.post("/api/v1/consultations")
    async def start() -> dict[str, bool]:
        return {"accepted": True}

    with TestClient(app) as client:
        assert client.post("/api/v1/consultations").status_code == 200
        response = client.post("/api/v1/consultations")

    assert response.status_code == 429
    assert response.json()["code"] == "CAPACITY_LIMIT_EXCEEDED"
