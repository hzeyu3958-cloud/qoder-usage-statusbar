"""Human-readable formatting for the Qoder usage snapshot."""

from __future__ import annotations

from .engine import Snapshot


def _fmt_credits(v: float) -> str:
    return f"{v:,.2f}"


def _fmt_duration(seconds) -> str:
    if seconds is None:
        return "-"
    if seconds < 60:
        return f"{seconds:.0f}s"
    m, s = divmod(int(seconds), 60)
    if m < 60:
        return f"{m}m{s:02d}s"
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m"


def ratio_color(ratio: float) -> str:
    """A coarse green->red bucket for context-window occupancy."""
    if ratio < 0.5:
        return "green"
    if ratio < 0.75:
        return "yellow"
    if ratio < 0.9:
        return "orange"
    return "red"


def one_line(snap: Snapshot) -> str:
    """Compact line for a tray title / status-bar text."""
    model = snap.current_model()
    ctx = snap.latest_context_ratio()
    return f"ctx {ctx*100:3.0f}% | +{_fmt_credits(snap.credits_session())}c | {model}"


def tooltip(snap: Snapshot) -> str:
    """Multi-line detail for the tray tooltip / CLI summary."""
    lines = [
        "Qoder usage",
        "-" * 24,
        f"model        : {snap.current_model()}",
        f"context now  : {snap.latest_context_ratio()*100:4.1f}%",
        f"context peak : {snap.peak_context_ratio()*100:4.1f}%",
        f"session cr   : {_fmt_credits(snap.credits_session())}",
        f"today cr     : {_fmt_credits(snap.credits_today())}",
        f"today reqs   : {snap.requests_today()}",
        f"avg turn     : {_fmt_duration(snap.avg_turn_seconds())}",
        f"updated      : {snap.generated_at:%H:%M:%S}",
    ]
    if snap.turns and snap.turns[-1].is_error:
        lines.append("! last request errored")
    return "\n".join(lines)
