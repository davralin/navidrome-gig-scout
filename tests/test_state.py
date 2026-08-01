from __future__ import annotations

import json
from pathlib import Path

import pytest

from navidrome_gig_scout.state import load_state, save_state


def test_state_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "state.json"

    save_state(path, {"event-id": "2026-08-01T12:34:56Z"})

    assert load_state(path) == {"event-id": "2026-08-01T12:34:56Z"}
    assert not path.with_suffix(".json.tmp").exists()


def test_load_state_rejects_non_object(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    path.write_text(json.dumps([]), encoding="utf-8")

    with pytest.raises(ValueError, match="JSON object"):
        load_state(path)
