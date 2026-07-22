FROM python:3.12-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY --from=ghcr.io/astral-sh/uv:0.8.4 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock* README.md ./
COPY src ./src

RUN uv sync --frozen --no-dev || uv sync --no-dev


FROM python:3.12-slim AS runtime

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN groupadd --system buildwise \
    && useradd --system --gid buildwise --create-home buildwise

WORKDIR /app

COPY --from=builder --chown=buildwise:buildwise /app/.venv /app/.venv
COPY --from=builder --chown=buildwise:buildwise /app/src /app/src
COPY --from=builder --chown=buildwise:buildwise /app/README.md /app/README.md

RUN mkdir -p /app/data \
    && chown -R buildwise:buildwise /app

USER buildwise

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["uvicorn", "buildwise.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
