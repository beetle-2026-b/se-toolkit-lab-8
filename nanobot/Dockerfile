# Multi-stage build for nanobot Docker deployment.
# Uses additional_contexts: workspace: . from docker-compose.yml
# so the build can access ../mcp and ../nanobot-websocket-channel.

# ---
# Stage 1: build the application in the `/app` directory.
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}astral/uv:python3.14-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Omit development dependencies
ENV UV_NO_DEV=1

# Disable Python downloads - use the system interpreter across both images.
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Copy workspace-level files (pyproject.toml, uv.lock from repo root)
COPY --from=workspace pyproject.toml uv.lock /app/

# Copy mcp directory (needed for lms-mcp editable install)
COPY --from=workspace mcp /app/mcp

# Copy nanobot-websocket-channel directory (needed for nanobot-webchat editable install)
COPY --from=workspace nanobot-websocket-channel /app/nanobot-websocket-channel

# Copy nanobot project files
COPY pyproject.toml /app/nanobot/pyproject.toml
COPY . /app/nanobot

# Install nanobot package with its own dependencies
WORKDIR /app/nanobot
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync
# Install mcp_lms package (for MCP server subprocess)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install /app/mcp
# Install mcp_observability package
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install /app/mcp/mcp_observability
# Install webchat packages with entry points
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install /app/nanobot-websocket-channel/nanobot-channel-protocol /app/nanobot-websocket-channel/nanobot-webchat
WORKDIR /app

# ---
# Stage 2: use a final image without uv
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}python:3.14.2-slim-bookworm

# Set environment variables for Python and application
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Make sure we use UTF-8 encoding
ENV LANG=C.UTF-8

# Setup a non-root user
RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

# Copy the application from the builder
COPY --from=builder --chown=nonroot:nonroot /app /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/nanobot"

# Use the non-root user to run our application
USER nonroot

WORKDIR /app

# Run the nanobot gateway via entrypoint.py
CMD ["python", "/app/nanobot/entrypoint.py"]
