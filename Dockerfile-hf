# We keep the slim base as it's the Archer's choice for a lean foundation.
FROM python:3.12-slim

# 1. SETTINGS: Standardizing the environment
ENV PYTHONUNBUFFERED=1 \
    GRADIO_SERVER_NAME="0.0.0.0" \
    GRADIO_SERVER_PORT=7860 \
    UV_PROJECT_ENVIRONMENT="/usr/local" 

# 2. SYSTEM: Install Supervisor
RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*

# 3. DIRECTORIES: Creating the structure
WORKDIR /app

# 4. PERMISSIONS: Create the HF user and take ownership of the app folder
# We do this BEFORE copying files so the user has rights to the directory
RUN useradd -m -u 1000 user && \
    mkdir -p /app/data /app/logs && \
    chown -R user:user /app

# Switch to the non-root user
USER user
ENV PATH="/home/user/.local/bin:${PATH}"

# 5. TOOLS: Install uv as the user
RUN pip install --no-cache-dir uv

# 6. DEPENDENCIES: Install using uv
COPY --chown=user:user pyproject.toml uv.lock ./
RUN uv pip install --system --no-cache -r pyproject.toml

# 7. CODE & DATA: Copy everything (including your pre-filled src/chroma_data)
# The --chown=user:user is CRITICAL here to avoid PermissionErrors
COPY --chown=user:user . .

# 8. CONFIG: Copy supervisor config
# (It's already covered by 'COPY . .', but explicit is fine)

EXPOSE 7860

# 9. EXECUTION: Start the Manager
CMD ["/usr/bin/supervisord", "-c", "/app/supervisord.conf"]