from fastapi import FastAPI
from fastapi.testclient import TestClient

from buildwise.observability.middleware import RequestContextMiddleware


def _client() -> TestClient:
    application = FastAPI()
    application.add_middleware(RequestContextMiddleware)

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return TestClient(application)


def test_request_context_generates_request_and_trace_headers() -> None:
    response = _client().get("/health")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    assert len(response.headers["X-Trace-ID"]) == 32


def test_request_context_preserves_caller_correlation_headers() -> None:
    response = _client().get(
        "/health",
        headers={
            "X-Request-ID": "request-from-client",
            "X-Trace-ID": "trace-from-client",
        },
    )

    assert response.headers["X-Request-ID"] == "request-from-client"
    assert response.headers["X-Trace-ID"] == "trace-from-client"
