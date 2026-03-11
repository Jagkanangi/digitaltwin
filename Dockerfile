# --- STAGE 1: BASE  ---
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./

# --- STAGE 2: RUN TESTS ---
FROM base AS development
RUN uv sync --frozen 
COPY src/ ./src/
COPY tests/ ./tests/
# If tests fail, the build will stop here
RUN uv run pytest tests/

# --- STAGE 3: PRODUCTION ---
FROM base AS production 
# 1. Install only production dependencies 
RUN uv sync --frozen --no-dev

# 2. Copy the source code 
COPY src/ ./src/

# 3. THE GPS: Set the PYTHONPATH 
# This allows 'from utils...' to work even though utils is inside src/
ENV PYTHONPATH="/app:/app/src"

# 4. THE ENTRYPOINT 
# Uses Cloud Run's $PORT or defaults to 8080 for local testing
CMD ["sh", "-c", "uv run uvicorn src.RestService:app --host 0.0.0.0 --port ${PORT:-8080}"]