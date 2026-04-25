# Railway-ready Dockerfile for excel-mcp-server
# Uses uv to install dependencies from pyproject.toml,
# then runs the server in streamable-http mode bound to Railway's $PORT.

FROM python:3.11-slim

# Install uv (fast Python package manager used by this project)
RUN pip install --no-cache-dir uv==0.5.4

WORKDIR /app

# Copy dependency manifests first to leverage Docker layer caching
COPY pyproject.toml uv.lock README.md ./
COPY src ./src

# Install the project's dependencies into a project-local .venv.
# We intentionally do NOT use --frozen so uv resolves freshly when
# pyproject.toml changes (e.g. when new deps like requests are added).
RUN uv sync --no-dev

# Default env vars (override in Railway Variables if needed)
#   EXCEL_FILES_PATH: where uploaded Excel files live (mount a Volume here)
#   FASTMCP_HOST    : must be 0.0.0.0 for Railway external traffic
ENV EXCEL_FILES_PATH=/data \
    FASTMCP_HOST=0.0.0.0

# Make sure the data directory exists (Railway Volume should mount on top of this)
RUN mkdir -p /data

# Railway injects PORT at runtime; fall back to 8000 for local docker run
CMD sh -c "FASTMCP_PORT=${PORT:-8000} uv run excel-mcp-server streamable-http"
