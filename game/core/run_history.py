from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class RunLogEntry:
    points: int
    mode: str
    highest_level: int
    coins_collected: int
    gemstones_collected: int
    duration_seconds: int
    outcome: str
    timestamp: str


def best_score_path(root: Path) -> Path:
    return root / "best_score.json"


def high_score_log_path(root: Path) -> Path:
    return root / "high_score_log.json"


def load_best_score(root: Path) -> int:
    try:
        path = best_score_path(root)
        if path.exists():
            return int(path.read_text(encoding="utf-8").strip() or 0)
    except Exception:
        pass
    return 0


def save_best_score(root: Path, score: int) -> None:
    try:
        best_score_path(root).write_text(str(max(0, int(score))), encoding="utf-8")
    except Exception:
        pass


def reset_best_score(root: Path) -> None:
    save_best_score(root, 0)


def load_run_history(root: Path) -> list[RunLogEntry]:
    try:
        path = high_score_log_path(root)
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = []
        for item in data:
            entries.append(
                RunLogEntry(
                    points=int(item.get("points", 0)),
                    mode=str(item.get("mode", "PLAYING")),
                    highest_level=int(item.get("highest_level", 1)),
                    coins_collected=int(item.get("coins_collected", 0)),
                    gemstones_collected=int(item.get("gemstones_collected", 0)),
                    duration_seconds=int(item.get("duration_seconds", 0)),
                    outcome=str(item.get("outcome", "UNKNOWN")),
                    timestamp=str(item.get("timestamp", "")),
                )
            )
        return entries
    except Exception:
        return []


def save_run_history(root: Path, entries: list[RunLogEntry]) -> None:
    payload = [asdict(entry) for entry in entries[:10]]
    try:
        high_score_log_path(root).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        pass


def add_run_entry(root: Path, *, points: int, mode: str, highest_level: int, coins_collected: int, gemstones_collected: int, duration_seconds: int, outcome: str) -> list[RunLogEntry]:
    timestamp = datetime.now().isoformat(timespec="seconds")
    entries = load_run_history(root)
    entries.append(
        RunLogEntry(
            points=max(0, int(points)),
            mode=mode,
            highest_level=max(1, int(highest_level)),
            coins_collected=max(0, int(coins_collected)),
            gemstones_collected=max(0, int(gemstones_collected)),
            duration_seconds=max(0, int(duration_seconds)),
            outcome=outcome,
            timestamp=timestamp,
        )
    )
    entries.sort(
        key=lambda entry: (
            entry.points,
            entry.highest_level,
            entry.coins_collected,
            -entry.duration_seconds,
        ),
        reverse=True,
    )
    trimmed = entries[:10]
    save_run_history(root, trimmed)
    save_best_score(root, trimmed[0].points if trimmed else 0)
    return trimmed
