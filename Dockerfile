FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install ONLY production dependencies into .venv
RUN uv sync --frozen --no-dev

# Activate the environment for all future commands
ENV VIRTUAL_ENV="/app/.venv"
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY src/ ./src/
copy data/ ./data/
ENV PYTHONPATH="/app:/app/src"

# Run the app using the already-installed uvicorn inside .venv
CMD ["sh", "-c", "uvicorn src.RestService:app --host 0.0.0.0 --port ${PORT:-8080}"]