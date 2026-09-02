from __future__ import annotations

from navidrome_gig_scout.ticketmaster import MIN_REQUEST_INTERVAL_SECONDS, parse_events


def test_ticketmaster_request_interval_is_below_provider_limit() -> None:
    assert MIN_REQUEST_INTERVAL_SECONDS == 1.0


def test_parse_events_extracts_core_fields() -> None:
    payload = {
        "_embedded": {
            "events": [
                {
                    "id": "abc",
                    "name": "Alestorm",
                    "url": "https://ticket.example.test",
                    "dates": {"start": {"dateTime": "2027-01-30T19:00:00Z"}},
                    "_embedded": {
                        "attractions": [{"name": "Alestorm"}, {"name": "Battle Beast"}],
                        "venues": [{"name": "O2 Forum Kentish Town"}],
                    },
                }
            ]
        }
    }

    events = parse_events(payload)

    assert len(events) == 1
    assert events[0].id == "abc"
    assert events[0].attractions == ("Alestorm", "Battle Beast")
    assert events[0].venue == "O2 Forum Kentish Town"
    assert events[0].date == "2027-01-30T19:00:00Z"


def test_parse_events_handles_empty_ticketmaster_response() -> None:
    assert parse_events({"page": {"totalElements": 0}}) == []
