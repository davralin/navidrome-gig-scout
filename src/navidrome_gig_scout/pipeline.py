from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from navidrome_gig_scout.config import Config
from navidrome_gig_scout.matching import is_exact_artist_match
from navidrome_gig_scout.notify import Notifier, build_notification
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
            notifications_sent=0,
            skipped=True,
        )

    matches = 0
    notifications_sent = 0
    for artist in artists:
        events = event_searcher(artist)
        LOGGER.debug("%s: %d Ticketmaster events", artist, len(events))
        for event in events:
            if is_exact_artist_match(artist, event):
                matches += 1
                notification = build_notification(artist, event)
                LOGGER.info(
                    "Match: %s | %s | %s | %s",
                    artist,
                    event.venue,
                    event.date,
                    event.url,
                )
                if dry_run:
                    LOGGER.info("Dry run: would notify %r", notification.title)
                elif notifier is not None and (
                    max_notifications is None or notifications_sent < max_notifications
                ):
                    if notifier.notify(notification):
                        notifications_sent += 1

    result = RunResult(
        artists=len(artists),
        matches=matches,
        notifications_sent=notifications_sent,
    )
    LOGGER.info(
        "Matches=%d notifications_sent=%d",
        result.matches,
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
