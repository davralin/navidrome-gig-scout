from __future__ import annotations

import pytest

from navidrome_gig_scout.config import ConfigError, load_config


def base_env() -> dict[str, str]:
    return {
        "NAVIDROME_URL": "https://navidrome.example.test/",
        "NAVIDROME_USER": "user",
        "NAVIDROME_PASS": "pass",
        "TICKETMASTER_API_KEY": "tm-key",
        "GEO_LAT": "51.5074",
        "GEO_LONG": "-0.1278",
        "RADIUS_MILES": "100",
        "LOOKAHEAD_DAYS": "365",
        "APPRISE_URLS": "json://example.test/a, json://example.test/b",
    }


def test_load_config_parses_required_values() -> None:
    config = load_config(base_env())

    assert config.navidrome_url == "https://navidrome.example.test"
    assert config.radius_miles == 100
    assert config.lookahead_days == 365
    assert config.apprise_urls == ("json://example.test/a", "json://example.test/b")
    assert config.log_level == "INFO"


def test_load_config_reports_missing_values() -> None:
    env = base_env()
    del env["NAVIDROME_PASS"]

    with pytest.raises(ConfigError, match="NAVIDROME_PASS"):
        load_config(env)


def test_load_config_validates_integer_values() -> None:
    env = base_env()
    env["LOOKAHEAD_DAYS"] = "soon"

    with pytest.raises(ConfigError, match="must be integers"):
        load_config(env)
