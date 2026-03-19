FROM python:3.13-slim

RUN pip install uv

WORKDIR /app
COPY pyproject.toml .
COPY *.py .

RUN uv sync

ENV AGENT_STATE_URL=http://agent:8001/session_state
ENV MCP_URL=http://mcp:8080/mcp/
ENV SYNC_POLL_INTERVAL=1.0

CMD ["uv", "run", "python", "main.py"]
