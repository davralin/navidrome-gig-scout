from __future__ import annotations

from navidrome_gig_scout.navidrome import make_token, parse_artists


def test_make_token_uses_subsonic_password_plus_salt_md5() -> None:
    assert make_token("password", "salt") == "b305cadbb3bce54f3aa59c64fec00dea"


def test_parse_artists_dedupes_and_sorts() -> None:
    payload = {
        "subsonic-response": {
            "status": "ok",
            "artists": {
                "index": [
                    {"artist": [{"name": "The Cure"}, {"name": "Alestorm"}]},
                    {"artist": [{"name": "the cure"}, {"name": "Alestorm"}, {"name": " "}]},
                ]
            },
        }
    }

    assert parse_artists(payload) == ["Alestorm", "The Cure"]
