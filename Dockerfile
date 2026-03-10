# --- STAGE 1: BASE  ---
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 \
    GRADIO_SERVER_NAME="0.0.0.0" \
    GRADIO_SERVER_PORT=7860
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./

# --- STAGE 2: RUN TESTS ---
FROM base AS development

RUN uv sync --frozen 
COPY src/ ./src/
COPY tests/ ./tests/
# We run the tests. If this fails, the build CRASHES here.
RUN uv run pytest tests/

# --- STAGE 3: PRODUCTION
FROM base AS production 
# We only install production dependencies
RUN uv sync --frozen --no-dev
# We ONLY copy the source code, NOT the tests
COPY src/ ./src/
# We run the app. 
CMD ["uv", "run", "python", "src/RestService.py"]