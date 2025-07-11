# ---------- builder ----------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ARG ENVIRONMENT=prod

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Disable Python downloads, because we want to use the system interpreter.
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /workspaces/fastapi-demo

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    if [ "$ENVIRONMENT" = "prod" ]; then \
    uv sync --frozen --no-install-project --no-editable --no-dev; \
    else \
    uv sync --frozen --no-install-project --all-extras; \
    fi

COPY . .

# Install the project
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$ENVIRONMENT" = "prod" ]; then \
    uv sync --frozen --no-editable --no-dev; \
    else \
    uv sync --frozen --all-extras; \
    fi

# ---------- production image ----------
FROM python:3.12-slim-bookworm AS prod

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd -r fastapi-demo && useradd -r -g fastapi-demo -M -s /usr/sbin/nologin fastapi-demo

RUN mkdir -p /workspaces/fastapi-demo && chown -R fastapi-demo:fastapi-demo /workspaces

WORKDIR /workspaces/fastapi-demo

# Pull in just the venv (with project code baked into site‑packages)
COPY --from=builder --chown=fastapi-demo:fastapi-demo /workspaces/fastapi-demo/.venv .venv

COPY --chown=fastapi-demo:fastapi-demo scripts scripts

COPY --chown=fastapi-demo:fastapi-demo alembic.ini alembic.ini

ENV PATH="/workspaces/fastapi-demo/.venv/bin:$PATH"

USER fastapi-demo

CMD ["uvicorn", "fastapi_demo.main:app", "--host", "0.0.0.0", "--port", "8080"]
# CMD ["uvicorn", "fastapi_demo.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]

# ---------- development image ----------
FROM python:3.12-slim-bookworm AS dev

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1000 fastapi-demo && useradd -m -u 1000 -g 1000 -r fastapi-demo

RUN mkdir -p /workspaces/fastapi-demo && chown -R fastapi-demo:fastapi-demo /workspaces

WORKDIR /workspaces/fastapi-demo

# Pull in the same venv (editable project install)
COPY --from=builder --chown=fastapi-demo:fastapi-demo /workspaces/fastapi-demo/.venv .venv

COPY --chown=fastapi-demo:fastapi-demo . .

ENV PATH="/workspaces/fastapi-demo/.venv/bin:$PATH"

USER fastapi-demo

CMD ["uvicorn", "fastapi_demo.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
# CMD ["uvicorn", "fastapi_demo.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000", "--reload"]
