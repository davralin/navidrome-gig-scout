from __future__ import annotations

from navidrome_gig_scout.notify import build_notification
from navidrome_gig_scout.ticketmaster import Event


def test_build_notification_contains_concert_details() -> None:
    event = Event(
        id="abc",
        name="Alestorm",
        attractions=("Alestorm",),
        venue="O2 Forum Kentish Town",
        date="2027-01-30T19:00:00Z",
        url="https://ticket.example.test",
    )

    notification = build_notification("Alestorm", event, "London")

    assert notification.title == "Concert match: Alestorm"
    assert "Artist: Alestorm" in notification.body
    assert "Venue: O2 Forum Kentish Town" in notification.body
    assert "Date: 2027-01-30T19:00:00Z" in notification.body
    assert "Search area: London" in notification.body
    assert "Tickets: https://ticket.example.test" in notification.body
