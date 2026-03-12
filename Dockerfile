FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY src/ ./src/
ENV PYTHONPATH="/app:/app/src"

# Activate the environment
ENV VIRTUAL_ENV="/app/.venv"
ENV PATH="/app/.venv/bin:$PATH"


# Cloud Run entrypoint
CMD ["sh", "-c", "uv run uvicorn src.RestService:app --host 0.0.0.0 --port ${PORT:-8080}"]