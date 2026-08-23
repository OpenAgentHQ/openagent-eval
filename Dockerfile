# Dockerfile for openagent_eval
# Multi-stage build with uv for fast dependency resolution
# Base image: python:3.11-slim (matches project's >=3.11 requirement)

# -------------------------------------------------------
# Stage 1: Build — Install dependencies with uv
# -------------------------------------------------------
FROM python:3.11-slim AS builder

# Install uv from the official astral-sh image
# https://github.com/astral-sh/uv
# Binary paths are /uv and /uvx in the distroless image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy project manifest files
COPY pyproject.toml uv.lock* ./

# Install only core dependencies for minimal image size
# --extra-group core matches the "core" extra in pyproject.toml:
#   typer, rich, pydantic, pyyaml, loguru, jinja2, httpx
# To include all extras, replace with: --all-extras
RUN uv pip install --system \
    --extra-group core \
    -r pyproject.toml

# Copy source code into the image
COPY openagent_eval/ /app/openagent_eval/

# -------------------------------------------------------
# Stage 2: Runtime — Minimal production image
# -------------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# Copy uv binary from builder for running the app
COPY --from=builder /bin/uv /bin/uv
COPY --from=builder /bin/uvx /bin/uvx

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/

# Copy application source code
COPY --from=builder /app/openagent_eval/ /app/openagent_eval/

# -------------------------------------------------------
# Entry point
# -------------------------------------------------------
# Use `uv run oaeval` to invoke the CLI entry point
# This ensures the correct environment (with all installed deps) is used
ENTRYPOINT ["uv", "run", "oaeval"]

# -------------------------------------------------------
# Optional: Health check
# -------------------------------------------------------
# Uncomment the following line if you want Docker to monitor container health
# HEALTHCHECK --interval=30s --timeout=5s CMD oaeval doctor

# -------------------------------------------------------
# Useful labels (optional but recommended)
# -------------------------------------------------------
LABEL \
    org.opencontainers.image.title="openagent-eval" \
    org.opencontainers.image.description="CLI framework for evaluating RAG systems and AI Agents" \
    org.opencontainers.image.version="0.4.10" \
    org.opencontainers.image.source="https://github.com/vellore-ws/openagent-eval"