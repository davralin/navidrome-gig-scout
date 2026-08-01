from __future__ import annotations

import logging
import re

from navidrome_gig_scout.ticketmaster import Event

LOGGER = logging.getLogger(__name__)


def normalize_artist(name: str) -> str:
    normalized = name.casefold().strip()
    normalized = re.sub(r"^the\s+", "", normalized)
    normalized = re.sub(r"[^\w\s]", "", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def is_exact_artist_match(artist: str, event: Event) -> bool:
    artist_normalized = normalize_artist(artist)
    attraction_normalized = [normalize_artist(attraction) for attraction in event.attractions]
    if artist_normalized in attraction_normalized:
        return True

    near_misses = [
        attraction
        for attraction, normalized in zip(event.attractions, attraction_normalized, strict=True)
        if artist_normalized in normalized or normalized in artist_normalized
    ]
    if near_misses:
        LOGGER.debug("Near miss for %r: %r", artist, near_misses)
    return False
