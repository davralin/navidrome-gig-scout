from __future__ import annotations

import logging
from dataclasses import dataclass

import apprise

from navidrome_gig_scout.ticketmaster import Event

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Notification:
    title: str
    body: str


def build_notification(artist: str, event: Event, search_place: str) -> Notification:
    return Notification(
        title=f"Concert match: {artist}",
        body="\n".join(
            [
                f"Artist: {artist}",
                f"Venue: {event.venue}",
                f"Date: {event.date}",
                f"Search area: {search_place}",
                f"Tickets: {event.url}",
            ]
        ),
    )


class Notifier:
    def __init__(self, urls: tuple[str, ...]) -> None:
        self._apprise = apprise.Apprise()
        for url in urls:
            if not self._apprise.add(url):
                raise ValueError(f"Invalid Apprise URL: {url}")

    def notify(self, notification: Notification) -> bool:
        sent = self._apprise.notify(
            title=notification.title,
            body=notification.body,
            body_format=apprise.NotifyFormat.TEXT,
        )
        if not sent:
            LOGGER.warning("Apprise notification returned false for %r", notification.title)
        return bool(sent)
