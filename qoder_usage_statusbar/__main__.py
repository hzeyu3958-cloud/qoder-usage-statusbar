"""Command-line entry point.

Usage:
    python -m qoder_usage_statusbar            # one-shot summary
    python -m qoder_usage_statusbar --watch    # live terminal status
    python -m qoder_usage_statusbar --tray     # system-tray icon
    python -m qoder_usage_statusbar --interval 10 --watch
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .cli import run_once, run_watch


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="qoder-usage-statusbar",
        description="Local credit/context status bar for Qoder (offline).",
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="print one summary (default)")
    mode.add_argument("--watch", action="store_true", help="live-updating terminal view")
    mode.add_argument("--tray", action="store_true", help="system-tray icon")
    p.add_argument("--interval", type=float, default=15.0,
                   help="refresh seconds for --watch/--tray (default 15)")
    p.add_argument("--version", action="version", version=__version__)
    args = p.parse_args(argv)

    if args.tray:
        from .tray import run_tray
        return run_tray(args.interval)
    if args.watch:
        return run_watch(args.interval)
    return run_once()


if __name__ == "__main__":
    sys.exit(main())
