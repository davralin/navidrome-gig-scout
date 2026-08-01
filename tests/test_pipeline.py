from __future__ import annotations

from pathlib import Path

from navidrome_gig_scout.config import Config
from navidrome_gig_scout.pipeline import run_pipeline
from navidrome_gig_scout.ticketmaster import Event


class FakeNotifier:
    def __init__(self) -> None:
        self.sent = 0

    def notify(self, notification: object) -> bool:
        self.sent += 1
        return True


def config(tmp_path: Path) -> Config:
    return Config(
        navidrome_url="https://navidrome.example.test",
        navidrome_user="user",
        navidrome_pass="pass",
        ticketmaster_api_key="key",
        geo_lat="51.5074",
        geo_long="-0.1278",
        radius_miles=100,
        lookahead_days=365,
        apprise_urls=("json://example.test",),
        state_path=tmp_path / "state.json",
        log_level="INFO",
        search_place="London",
    )


def matching_event(event_id: str = "abc") -> Event:
    return Event(
        id=event_id,
        name="Alestorm",
        attractions=("Alestorm",),
        venue="O2 Forum Kentish Town",
        date="2027-01-30T19:00:00Z",
        url="https://ticket.example.test",
    )


def test_dry_run_does_not_write_state(tmp_path: Path) -> None:
    cfg = config(tmp_path)
    notifier = FakeNotifier()

    result = run_pipeline(
        config=cfg,
        artist_fetcher=lambda: ["Alestorm"],
        event_searcher=lambda artist: [matching_event()],
        notifier=notifier,  # type: ignore[arg-type]
        dry_run=True,
    )

    assert result.new == 1
    assert result.notifications_sent == 0
    assert notifier.sent == 0
    assert not cfg.state_path.exists()


def test_real_run_writes_state_and_skips_second_run(tmp_path: Path) -> None:
    cfg = config(tmp_path)
    notifier = FakeNotifier()

    first = run_pipeline(
        config=cfg,
        artist_fetcher=lambda: ["Alestorm"],
        event_searcher=lambda artist: [matching_event()],
        notifier=notifier,  # type: ignore[arg-type]
        dry_run=False,
    )
    second = run_pipeline(
        config=cfg,
        artist_fetcher=lambda: ["Alestorm"],
        event_searcher=lambda artist: [matching_event()],
        notifier=notifier,  # type: ignore[arg-type]
        dry_run=False,
    )

    assert first.new == 1
    assert first.notifications_sent == 1
    assert second.new == 0
    assert second.already_notified == 1
    assert notifier.sent == 1


def test_max_notifications_limits_sends_but_records_state(tmp_path: Path) -> None:
    cfg = config(tmp_path)
    notifier = FakeNotifier()

    result = run_pipeline(
        config=cfg,
        artist_fetcher=lambda: ["Alestorm"],
        event_searcher=lambda artist: [matching_event("one"), matching_event("two")],
        notifier=notifier,  # type: ignore[arg-type]
        dry_run=False,
        max_notifications=1,
    )

    assert result.new == 2
    assert result.notifications_sent == 1
    assert notifier.sent == 1
