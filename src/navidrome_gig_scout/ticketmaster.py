from __future__ import annotations

import datetime as dt
import time
from dataclasses import dataclass
from typing import Any

import requests

DISCOVERY_URL = "https://app.ticketmaster.com/discovery/v2/events.json"
MAX_DAILY_REQUESTS = 5000
MIN_REQUEST_INTERVAL_SECONDS = 0.2


@dataclass(frozen=True)
class Event:
    id: str
    name: str
    attractions: tuple[str, ...]
    venue: str
    date: str
    url: str


class TicketmasterClient:
    def __init__(self, api_key: str, session: requests.Session) -> None:
        self._api_key = api_key
        self._session = session
        self._last_request_at = 0.0

    def search_events(
        self,
        *,
        artist: str,
        lat: str,
        long: str,
        radius_miles: int,
        lookahead_days: int,
    ) -> list[Event]:
        now = dt.datetime.now(dt.UTC).replace(microsecond=0)
        end = now + dt.timedelta(days=lookahead_days)
        self._throttle()
        response = self._session.get(
            DISCOVERY_URL,
            params={
                "apikey": self._api_key,
                "keyword": artist,
                "latlong": f"{lat},{long}",
                "radius": str(radius_miles),
                "unit": "miles",
                "startDateTime": now.isoformat().replace("+00:00", "Z"),
                "endDateTime": end.isoformat().replace("+00:00", "Z"),
                "classificationName": "Music",
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Ticketmaster response must be a JSON object")
        return parse_events(payload)

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if self._last_request_at and elapsed < MIN_REQUEST_INTERVAL_SECONDS:
            time.sleep(MIN_REQUEST_INTERVAL_SECONDS - elapsed)
        self._last_request_at = time.monotonic()


def parse_events(payload: dict[str, Any]) -> list[Event]:
    embedded = payload.get("_embedded")
    if not isinstance(embedded, dict):
        return []
    events = embedded.get("events", [])
    if not isinstance(events, list):
        return []
    return [event for item in events if isinstance(item, dict) if (event := parse_event(item))]


def parse_event(item: dict[str, Any]) -> Event | None:
    event_id = item.get("id")
    if not isinstance(event_id, str) or not event_id:
        return None
    return Event(
        id=event_id,
        name=str(item.get("name") or ""),
        attractions=extract_attractions(item),
        venue=extract_venue(item),
        date=extract_date(item),
        url=str(item.get("url") or ""),
    )


def extract_attractions(item: dict[str, Any]) -> tuple[str, ...]:
    embedded = item.get("_embedded")
    if not isinstance(embedded, dict):
        return ()
    attractions = embedded.get("attractions", [])
    if not isinstance(attractions, list):
        return ()
    return tuple(
        attraction["name"]
        for attraction in attractions
        if isinstance(attraction, dict) and isinstance(attraction.get("name"), str)
    )


def extract_venue(item: dict[str, Any]) -> str:
    embedded = item.get("_embedded")
    if not isinstance(embedded, dict):
        return "Unknown venue"
    venues = embedded.get("venues", [])
    if isinstance(venues, list) and venues and isinstance(venues[0], dict):
        return str(venues[0].get("name") or "Unknown venue")
    return "Unknown venue"


def extract_date(item: dict[str, Any]) -> str:
    dates = item.get("dates")
    if not isinstance(dates, dict):
        return "Unknown date"
    start = dates.get("start")
    if not isinstance(start, dict):
        return "Unknown date"
    return str(start.get("dateTime") or start.get("localDate") or "Unknown date")
