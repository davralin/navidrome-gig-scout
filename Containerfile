FROM ghcr.io/astral-sh/uv:0.13.7@sha256:96f40d3904aad8d0bd010539001d36c8e2188b981e1334471a90c4a1d93bb490 AS uv
FROM docker.io/library/python:3.15-alpine@sha256:a0f2e268f2ce8f3709611a90054ec6a8ae31f6251f5896b8648b9bb99835e30a AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

COPY --from=uv /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN uv sync --frozen --no-dev --no-editable \
    && find /app -type d -name __pycache__ -prune -exec rm -rf {} +

FROM docker.io/library/python:3.15-alpine@sha256:a0f2e268f2ce8f3709611a90054ec6a8ae31f6251f5896b8648b9bb99835e30a

LABEL org.opencontainers.image.title="navidrome-gig-scout"
LABEL org.opencontainers.image.description="Notify when Navidrome artists have nearby Ticketmaster concerts."

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup -g 1000 -S app \
    && adduser -u 1000 -S -G app -h /home/app -s /sbin/nologin app \
    && rm -rf /usr/local/bin/pip* \
        /usr/local/lib/python3.14/ensurepip \
        /usr/local/lib/python3.14/site-packages/pip* \
    && chown -R app:app /app

COPY --from=builder --chown=app:app /app /app

HEALTHCHECK NONE

USER app:app

ENTRYPOINT ["/app/.venv/bin/gig-scout"]
