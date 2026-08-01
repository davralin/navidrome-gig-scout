from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

REQUIRED_ENV = (
    "NAVIDROME_URL",
    "NAVIDROME_USER",
    "NAVIDROME_PASS",
    "TICKETMASTER_API_KEY",
    "GEO_LAT",
    "GEO_LONG",
    "RADIUS_MILES",
    "LOOKAHEAD_DAYS",
    "APPRISE_URLS",
)


@dataclass(frozen=True)
class Config:
    navidrome_url: str
    navidrome_user: str
    navidrome_pass: str
    ticketmaster_api_key: str
    geo_lat: str
    geo_long: str
    radius_miles: int
    lookahead_days: int
    apprise_urls: tuple[str, ...]
    state_path: Path
    log_level: str
    search_place: str


class ConfigError(ValueError):
    pass


def load_config(env: Mapping[str, str] | None = None) -> Config:
    values = env if env is not None else os.environ
    missing = [name for name in REQUIRED_ENV if not values.get(name)]
    if missing:
        raise ConfigError(f"Missing required environment variables: {', '.join(missing)}")

    try:
        radius_miles = int(values["RADIUS_MILES"])
        lookahead_days = int(values["LOOKAHEAD_DAYS"])
    except ValueError as exc:
        raise ConfigError("RADIUS_MILES and LOOKAHEAD_DAYS must be integers") from exc

    if radius_miles <= 0:
        raise ConfigError("RADIUS_MILES must be greater than 0")
    if lookahead_days <= 0:
        raise ConfigError("LOOKAHEAD_DAYS must be greater than 0")

    apprise_urls = tuple(url.strip() for url in values["APPRISE_URLS"].split(",") if url.strip())
    if not apprise_urls:
        raise ConfigError("APPRISE_URLS must contain at least one URL")

    log_level = values.get("LOG_LEVEL", "INFO").upper()
    if logging.getLevelName(log_level) == f"Level {log_level}":
        raise ConfigError(f"Invalid LOG_LEVEL: {log_level}")

    return Config(
        navidrome_url=values["NAVIDROME_URL"].rstrip("/"),
        navidrome_user=values["NAVIDROME_USER"],
        navidrome_pass=values["NAVIDROME_PASS"],
        ticketmaster_api_key=values["TICKETMASTER_API_KEY"],
        geo_lat=values["GEO_LAT"],
        geo_long=values["GEO_LONG"],
        radius_miles=radius_miles,
        lookahead_days=lookahead_days,
        apprise_urls=apprise_urls,
        state_path=Path(values.get("STATE_PATH", "/data/state.json")),
        log_level=log_level,
        search_place=values.get("SEARCH_PLACE", f"{values['GEO_LAT']},{values['GEO_LONG']}"),
    )
