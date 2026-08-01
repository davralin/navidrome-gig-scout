from __future__ import annotations

import argparse
import logging

import requests

from navidrome_gig_scout.config import ConfigError, load_config
from navidrome_gig_scout.navidrome import fetch_artists
from navidrome_gig_scout.notify import Notifier
from navidrome_gig_scout.pipeline import make_event_searcher, run_pipeline
from navidrome_gig_scout.ticketmaster import TicketmasterClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find nearby Ticketmaster concerts for Navidrome artists."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Log notifications and do not write state"
    )
    parser.add_argument(
        "--max-notifications", type=int, help="Maximum notifications to send this run"
    )
    parser.add_argument("--artist-limit", type=int, help="Limit artists for local testing")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_config()
    except ConfigError as exc:
        raise SystemExit(str(exc)) from exc

    logging.basicConfig(
        level=getattr(logging, config.log_level), format="%(levelname)s %(message)s"
    )

    with requests.Session() as session:
        artist_fetcher = lambda: fetch_artists(  # noqa: E731 - keeps dependency wiring local and explicit.
            config.navidrome_url,
            config.navidrome_user,
            config.navidrome_pass,
            session,
        )
        ticketmaster = TicketmasterClient(config.ticketmaster_api_key, session)
        notifier = None if args.dry_run else Notifier(config.apprise_urls)
        run_pipeline(
            config=config,
            artist_fetcher=artist_fetcher,
            event_searcher=make_event_searcher(config, ticketmaster),
            notifier=notifier,
            dry_run=args.dry_run,
            max_notifications=args.max_notifications,
            artist_limit=args.artist_limit,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
