"""qoder-usage-statusbar :: data engine

Scan Qoder's local session logs (JSONL) and aggregate the *reliable* local
metrics:

  * credits consumed (per request / per session / today)
  * context-window occupancy ratio (latest / peak)
  * request counts and per-turn wall-clock duration
  * model currently in use

Note: Qoder deliberately zeroes ``input_tokens`` / ``output_tokens`` /
``cache_*`` in the on-disk logs, so real token counts and tok/s are NOT
derivable here. We surface ``credits`` (which IS populated) instead.
Everything is read locally -- no network calls.
"""

from __future__ import annotations

import glob
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, Optional


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def default_roots() -> list[Path]:
    """Candidate Qoder data dirs across products, in priority order."""
    home = Path.home()
    candidates = [
        home / ".qoderworkcn",
        home / ".qoder",
    ]
    return [c for c in candidates if c.is_dir()]


def _project_dirs(root: Path) -> list[Path]:
    p = root / "projects"
    return [p] if p.is_dir() else []


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

@dataclass
class Turn:
    session_id: str
    ts: datetime
    model: str
    credits: float
    original_credits: float
    billable: bool
    context_ratio: float
    is_error: bool


@dataclass
class Snapshot:
    generated_at: datetime
    turns: list[Turn] = field(default_factory=list)

    # ---- aggregates ----
    def today(self) -> list[Turn]:
        # logs are UTC; compare calendar days in the local timezone
        local_tz = self.generated_at.tzinfo
        d = self.generated_at.astimezone(local_tz).date()
        return [t for t in self.turns
                if t.ts.astimezone(local_tz).date() == d]

    def session(self, session_id: str) -> list[Turn]:
        return [t for t in self.turns if t.session_id == session_id]

    def latest_session(self) -> Optional[str]:
        if not self.turns:
            return None
        return max(self.turns, key=lambda t: t.ts).session_id

    def credits_today(self) -> float:
        return sum(t.credits for t in self.today())

    def credits_session(self) -> float:
        sid = self.latest_session()
        if sid is None:
            return 0.0
        return sum(t.credits for t in self.session(sid))

    def requests_today(self) -> int:
        return len(self.today())

    def peak_context_ratio(self) -> float:
        sid = self.latest_session()
        turns = self.session(sid) if sid else []
        return max((t.context_ratio for t in turns), default=0.0)

    def latest_context_ratio(self) -> float:
        if not self.turns:
            return 0.0
        return max(self.turns, key=lambda t: t.ts).context_ratio

    def current_model(self) -> str:
        if not self.turns:
            return "-"
        return max(self.turns, key=lambda t: t.ts).model

    def avg_turn_seconds(self) -> Optional[float]:
        """Mean wall-clock gap between consecutive turns in the latest session."""
        sid = self.latest_session()
        turns = sorted(self.session(sid), key=lambda t: t.ts)
        if len(turns) < 2:
            return None
        gaps = [(b.ts - a.ts).total_seconds() for a, b in zip(turns, turns[1:])]
        gaps = [g for g in gaps if 0 < g < 6 * 3600]  # drop idle spikes
        return sum(gaps) / len(gaps) if gaps else None


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _parse_ts(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _iter_jsonl(path: Path) -> Iterator[dict]:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                line = line.strip()
                if not line or '"usage"' not in line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    except OSError:
        return


def _turn_from_record(rec: dict) -> Optional[Turn]:
    if rec.get("type") != "assistant":
        return None
    msg = rec.get("message")
    if not isinstance(msg, dict):
        return None
    usage = msg.get("usage")
    if not isinstance(usage, dict):
        return None
    ts = _parse_ts(rec.get("timestamp", ""))
    if ts is None:
        return None
    return Turn(
        session_id=rec.get("sessionId", "?"),
        ts=ts,
        model=msg.get("model") or "?",
        credits=float(usage.get("credits", 0) or 0),
        original_credits=float(usage.get("original_credits", 0) or 0),
        billable=bool(usage.get("billable", False)),
        context_ratio=float(usage.get("context_usage_ratio", 0) or 0),
        is_error=bool(rec.get("isApiErrorMessage", False)),
    )


def scan_turns(roots: Optional[Iterable[Path]] = None,
               include_subagents: bool = True) -> list[Turn]:
    roots = list(roots) if roots else default_roots()
    turns: list[Turn] = []
    seen: set[tuple] = set()
    for root in roots:
        pattern = "projects/**/*.jsonl" if include_subagents else "projects/*/*.jsonl"
        for path in glob.glob(str(root / pattern), recursive=True):
            for rec in _iter_jsonl(Path(path)):
                turn = _turn_from_record(rec)
                if turn is None:
                    continue
                key = (turn.session_id, turn.ts.isoformat(), turn.model)
                if key in seen:
                    continue
                seen.add(key)
                turns.append(turn)
    turns.sort(key=lambda t: t.ts)
    return turns


def build_snapshot(roots: Optional[Iterable[Path]] = None) -> Snapshot:
    turns = scan_turns(roots)
    now = datetime.now().astimezone()
    return Snapshot(generated_at=now, turns=turns)
