from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from typing import Protocol

from navidrome_gig_scout.config import Config
from navidrome_gig_scout.matching import is_exact_artist_match
from navidrome_gig_scout.notify import Notifier, build_notification
from navidrome_gig_scout.state import load_state, save_state
from navidrome_gig_scout.ticketmaster import MAX_DAILY_REQUESTS, Event, TicketmasterClient

LOGGER = logging.getLogger(__name__)


class ArtistFetcher(Protocol):
    def __call__(self) -> list[str]: ...


class EventSearcher(Protocol):
    def __call__(self, artist: str) -> list[Event]: ...


@dataclass(frozen=True)
class RunResult:
    artists: int
    matches: int
    new: int
    already_notified: int
    notifications_sent: int
    skipped: bool = False


def run_pipeline(
    *,
    config: Config,
    artist_fetcher: ArtistFetcher,
    event_searcher: EventSearcher,
    notifier: Notifier | None,
    dry_run: bool,
    max_notifications: int | None = None,
    artist_limit: int | None = None,
) -> RunResult:
    state = load_state(config.state_path)
    artists = artist_fetcher()
    if artist_limit is not None:
        artists = artists[:artist_limit]
    LOGGER.info("Loaded %d Navidrome artists", len(artists))

    if len(artists) > MAX_DAILY_REQUESTS:
        LOGGER.warning(
            "Artist count %d exceeds Ticketmaster %d/day guard; skipping",
            len(artists),
            MAX_DAILY_REQUESTS,
        )
        return RunResult(
            artists=len(artists),
            matches=0,
            new=0,
            already_notified=0,
            notifications_sent=0,
            skipped=True,
        )

    matches: list[tuple[str, Event]] = []
    for artist in artists:
        events = event_searcher(artist)
        LOGGER.debug("%s: %d Ticketmaster events", artist, len(events))
        for event in events:
            if is_exact_artist_match(artist, event):
                matches.append((artist, event))

    notified_at = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    new = 0
    already_notified = 0
    notifications_sent = 0
    for artist, event in matches:
        if event.id in state:
            already_notified += 1
            LOGGER.info("Already notified: %s | %s | %s", artist, event.venue, event.date)
            continue

        new += 1
        notification = build_notification(artist, event, config.search_place)
        LOGGER.info("New match: %s | %s | %s | %s", artist, event.venue, event.date, event.url)
        if dry_run:
            LOGGER.info("Dry run: would notify %r", notification.title)
        elif notifier is not None and (
            max_notifications is None or notifications_sent < max_notifications
        ):
            if notifier.notify(notification):
                notifications_sent += 1
        state[event.id] = notified_at

    if dry_run:
        LOGGER.info("Dry run: state unchanged: %s", config.state_path)
    else:
        save_state(config.state_path, state)
        LOGGER.info("Wrote state: %s", config.state_path)

    result = RunResult(
        artists=len(artists),
        matches=len(matches),
        new=new,
        already_notified=already_notified,
        notifications_sent=notifications_sent,
    )
    LOGGER.info(
        "Matches=%d new=%d already_notified=%d notifications_sent=%d",
        result.matches,
        result.new,
        result.already_notified,
        result.notifications_sent,
    )
    return result


def make_event_searcher(config: Config, client: TicketmasterClient) -> EventSearcher:
    def search(artist: str) -> list[Event]:
        return client.search_events(
            artist=artist,
            lat=config.geo_lat,
            long=config.geo_long,
            radius_miles=config.radius_miles,
            lookahead_days=config.lookahead_days,
        )

    return search
