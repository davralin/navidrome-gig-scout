from __future__ import annotations

import logging

import pytest

from navidrome_gig_scout.matching import is_exact_artist_match, normalize_artist
from navidrome_gig_scout.ticketmaster import Event


def event(*attractions: str) -> Event:
    return Event(
        id="event-id",
        name="event",
        attractions=attractions,
        venue="venue",
        date="2027-01-30T19:00:00Z",
        url="https://example.test",
    )


def test_normalize_artist_strips_the_and_punctuation() -> None:
    assert normalize_artist("The Cure!") == "cure"
    assert normalize_artist(" AC/DC ") == "acdc"


def test_exact_match_after_normalization() -> None:
    assert is_exact_artist_match("The Cure", event("Cure"))


def test_rejects_non_exact_near_miss(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)

    assert not is_exact_artist_match("Ghost", event("Ghost Hounds"))
    assert "Near miss" in caplog.text
