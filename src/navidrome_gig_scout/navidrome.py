from __future__ import annotations

import hashlib
import secrets
import string
from typing import Any

import requests

SUBSONIC_VERSION = "1.16.1"
CLIENT_NAME = "gig-scout"


def make_token(password: str, salt: str) -> str:
    return hashlib.md5(f"{password}{salt}".encode()).hexdigest()  # noqa: S324 - Subsonic requires MD5 token auth.


def make_salt(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def parse_artists(payload: dict[str, Any]) -> list[str]:
    response = payload.get("subsonic-response")
    if not isinstance(response, dict):
        raise ValueError("Navidrome response is missing subsonic-response")
    if response.get("status") != "ok":
        raise ValueError(f"Navidrome returned non-ok response: {response!r}")

    names: dict[str, str] = {}
    artists = response.get("artists", {})
    indexes = artists.get("index", []) if isinstance(artists, dict) else []
    for index in indexes:
        if not isinstance(index, dict):
            continue
        for artist in index.get("artist", []):
            if isinstance(artist, dict) and isinstance(artist.get("name"), str):
                name = artist["name"].strip()
                if name:
                    names.setdefault(name.casefold(), name)
    return sorted(names.values(), key=str.casefold)


def fetch_artists(base_url: str, user: str, password: str, session: requests.Session) -> list[str]:
    salt = make_salt()
    response = session.get(
        f"{base_url.rstrip('/')}/rest/getArtists.view",
        params={
            "u": user,
            "t": make_token(password, salt),
            "s": salt,
            "v": SUBSONIC_VERSION,
            "c": CLIENT_NAME,
            "f": "json",
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Navidrome response must be a JSON object")
    return parse_artists(payload)
