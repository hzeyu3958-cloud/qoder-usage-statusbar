"""Terminal entry points: one-shot print and live watch."""

from __future__ import annotations

import os
import sys
import time

from .engine import build_snapshot
from .format import tooltip, one_line


def _clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def run_once() -> int:
    snap = build_snapshot()
    print(tooltip(snap))
    print()
    print(one_line(snap))
    return 0


def run_watch(interval: float) -> int:
    try:
        while True:
            snap = build_snapshot()
            _clear()
            print(tooltip(snap))
            print()
            print(one_line(snap))
            print(f"\n(refresh every {interval:.0f}s, Ctrl+C to quit)")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nbye")
        return 0
