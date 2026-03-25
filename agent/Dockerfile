# ── Stage 1: Install Python dependencies ───────────────────────────────────
FROM python:3.13-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copy local binary packages (referenced as ../223p/bin/* in pyproject.toml)
COPY 223p/bin/ ./223p/bin/

# Copy dependency manifests
COPY agent/pyproject.toml agent/uv.lock ./agent/

# Install production dependencies (no dev group, no project package itself)
WORKDIR /app/agent
RUN uv sync --frozen --no-dev --no-install-project

# ── Stage 2: Runtime image ──────────────────────────────────────────────────
FROM python:3.13-slim AS runner
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# All agent modules are importable as top-level packages (e.g. master_architecture, sub_agents)
ENV PYTHONPATH=/app/agent
ENV PORT=8001

WORKDIR /app

# Copy uv (used to execute the venv's Python cleanly)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy 223p binary packages (required by the bob / scratch packages at import time)
COPY 223p/bin/ ./223p/bin/

# Copy the virtual environment produced by the builder stage
COPY --from=builder /app/agent/.venv ./agent/.venv

# Install Playwright browser binaries + required system libraries.
# playwright is used in production (capture_frontend_state_tool.py), so Chromium
# must be present at runtime. --with-deps runs apt-get inside this stage.
RUN /app/agent/.venv/bin/playwright install --with-deps chromium

# Copy all agent source code
COPY agent/ ./agent/

# Remove test files — they are not needed at runtime
RUN rm -rf /app/agent/tests/

# Create the uploads mount point (bind-mounted from ./mapper/uploads at runtime)
RUN mkdir -p /app/uploads

WORKDIR /app/agent
EXPOSE 8001
CMD [".venv/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
