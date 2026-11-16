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

# Copy project manifest files (README.md is required by hatchling metadata)
COPY pyproject.toml uv.lock* README.md ./

# Install core dependencies first (cached layer — only re-runs when this
# line changes). These mirror the base `dependencies` in pyproject.toml.
# To include all extras instead, use: uv pip install --system --all-extras .
RUN uv pip install --system --no-cache \
    "typer>=0.12.0" \
    "rich>=13.0.0" \
    "pydantic>=2.0.0" \
    "pyyaml>=6.0" \
    "loguru>=0.7.0" \
    "jinja2>=3.1.0" \
    "httpx>=0.27.0"

# Copy source code into the image
COPY openagent_eval/ /app/openagent_eval/

# Install the package itself (creates the `oaeval` console script).
# --no-deps skips re-resolving the deps installed above, keeping this fast.
RUN uv pip install --system --no-cache --no-deps .

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
# `oaeval` console script is installed system-wide in site-packages
ENTRYPOINT ["oaeval"]

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