FROM ghcr.io/astral-sh/uv:0.12.1@sha256:cf4eedcaa81655197f625739489effcbe71b61ceb1506f332c3facae5deceded AS uv
FROM docker.io/library/python:3.14-slim@sha256:cea0e6040540fb2b965b6e7fb5ffa00871e632eef63719f0ea54bca189ce14a6

LABEL org.opencontainers.image.title="navidrome-gig-scout"
LABEL org.opencontainers.image.description="Notify when Navidrome artists have nearby Ticketmaster concerts."

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

COPY --from=uv /uv /usr/local/bin/uv

WORKDIR /app

RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --home-dir /home/app --create-home --shell /usr/sbin/nologin app \
    && mkdir -p /data \
    && chown -R app:app /app /data

COPY --chown=app:app pyproject.toml uv.lock README.md ./
COPY --chown=app:app src ./src

RUN uv sync --frozen --no-dev --no-editable \
    && find /app -type d -name __pycache__ -prune -exec rm -rf {} + \
    && chown -R app:app /app

HEALTHCHECK NONE

USER app:app

ENTRYPOINT ["/app/.venv/bin/gig-scout"]
