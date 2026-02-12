# Use a lightweight Python image
FROM python:3.13-slim

# Prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install dependencies using pyproject.toml
COPY mcp_server/pyproject.toml mcp_server/uv.lock ./
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy the entire mcp_server package to preserve structure
# We assume .dockerignore excludes .venv, __pycache__, etc.
COPY mcp_server ./mcp_server

# Set PYTHONPATH so python can find the mcp_server package
ENV PYTHONPATH=/app

# Expose the port
EXPOSE 8080

# Run the application
# Note: mcp_server.server.main is the module path
CMD ["uvicorn", "mcp_server.server.main:app", "--host", "0.0.0.0", "--port", "8080"]