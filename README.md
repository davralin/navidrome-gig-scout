# Navidrome Gig Scout

`navidrome-gig-scout` checks the artists in a Navidrome library against the
Ticketmaster Discovery API and sends Apprise notifications for new exact artist matches.

The program runs once and exits. It is intended for local testing, containers, and later
Kubernetes CronJob deployment.

## Matching

Artist matching is intentionally conservative:

- lowercase both names
- strip a leading `The `
- strip punctuation
- collapse whitespace
- require an exact normalized artist-to-attraction match

There is no fuzzy matching or Levenshtein matching. Near misses are logged at `DEBUG`.

## Configuration

Required environment variables:

- `NAVIDROME_URL`
- `NAVIDROME_USER`
- `NAVIDROME_PASS`
- `TICKETMASTER_API_KEY`
- `GEO_LAT`
- `GEO_LONG`
- `RADIUS_MILES`
- `LOOKAHEAD_DAYS`
- `APPRISE_URLS`, comma-separated

Optional environment variables:

- `STATE_PATH`, default `/data/state.json`
- `LOG_LEVEL`, default `INFO`
- `SEARCH_PLACE`, default `<GEO_LAT>,<GEO_LONG>`

The state file is a flat JSON object mapping Ticketmaster event IDs to the ISO timestamp when
they were recorded. Losing it does not break the app, but matching future runs may notify again
for events that were previously sent.

## Local Development

Local source execution requires Python 3.14 and `uv`.

```sh
uv sync
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/
uv run pytest tests/ -v
```

Example dry-run:

```sh
STATE_PATH=.local/state.json \
LOG_LEVEL=DEBUG \
uv run gig-scout --dry-run --artist-limit 50
```

Dry-run logs matching notifications and does not write state.

To send at most one notification during local testing:

```sh
STATE_PATH=.local/state.json \
uv run gig-scout --max-notifications 1
```

## Container

Running the container does not require host Python. The image contains Python 3.14.

Build locally:

```sh
docker build -f Containerfile -t navidrome-gig-scout:local .
```

Run a dry-run with local state mounted to `/data`:

```sh
docker run --rm \
  --env-file .env \
  -e STATE_PATH=/data/state.json \
  -v "$PWD/.local:/data" \
  navidrome-gig-scout:local \
  --dry-run --artist-limit 50
```

## API Behavior

Navidrome is queried with Subsonic legacy token auth via `getArtists.view`.

Ticketmaster is queried once per artist with `classificationName=Music`, the configured
`latlong`, radius in miles, and a `startDateTime`/`endDateTime` window from now through
`LOOKAHEAD_DAYS`.

Requests are throttled to at most 5 per second. If the Navidrome artist count exceeds 5000,
the run logs a warning and exits successfully without querying Ticketmaster.
