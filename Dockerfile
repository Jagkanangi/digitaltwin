# ============================
# STAGE 1 — BASE
# ============================
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./

# # ============================
# # STAGE 2 — BUILDER (NO TESTS)
# # ============================
# # This stage isolates dependency resolution so production never touches the test stage.
# FROM base AS builder
RUN uv sync --frozen --no-dev
COPY src/ ./src/
ENV PYTHONPATH="/app:/app/src"

# ============================
# STAGE 3 — DEVELOPMENT (TESTS)
# ============================
# This stage ONLY runs in CI when explicitly targeted.
# FROM base AS development
# # RUN uv sync --frozen
# COPY tests/ ./tests/
# RUN uv run pytest tests/

# ============================
# STAGE 4 — PRODUCTION
# ============================
FROM base AS production

# Cloud Run entrypoint
CMD ["sh", "-c", "uv run uvicorn src.RestService:app --host 0.0.0.0 --port ${PORT:-8080}"]