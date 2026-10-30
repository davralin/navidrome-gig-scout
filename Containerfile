FROM ghcr.io/astral-sh/uv:0.12.13@sha256:b485bd65cc2cf1c9a93b3554012c9c3778cf7b1b5fd3d3096ce9e1226c97e1e6 AS uv
FROM docker.io/library/python:3.15-alpine@sha256:20a82dbc2783112ddb91d1534603f802d222a3e63e593cd002eb2ac534e70211 AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

COPY --from=uv /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN uv sync --frozen --no-dev --no-editable \
    && find /app -type d -name __pycache__ -prune -exec rm -rf {} +

FROM docker.io/library/python:3.15-alpine@sha256:20a82dbc2783112ddb91d1534603f802d222a3e63e593cd002eb2ac534e70211

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
