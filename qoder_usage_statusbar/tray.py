"""System-tray status item (Windows / macOS / Linux).

Requires:  pip install pystray Pillow
The tray tooltip shows the full summary; the icon is a circle whose colour
reflects context-window occupancy (green -> red).
"""

from __future__ import annotations

import threading

from .engine import build_snapshot
from .format import one_line, tooltip, ratio_color

_COLOR = {
    "green": (46, 204, 113),
    "yellow": (241, 196, 15),
    "orange": (230, 126, 34),
    "red": (231, 76, 60),
}


def _make_image(ratio: float):
    from PIL import Image, ImageDraw

    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rgb = _COLOR[ratio_color(ratio)]
    d.ellipse((6, 6, size - 6, size - 6), fill=rgb + (255,),
              outline=(255, 255, 255, 220), width=3)
    return img


def run_tray(interval: float) -> int:
    try:
        import pystray
    except ImportError:
        print("pystray/Pillow not installed. Run: pip install pystray Pillow")
        print("Falling back to terminal watch mode.\n")
        from .cli import run_watch
        return run_watch(interval)

    state = {"snapshot": None, "stop": threading.Event()}

    def refresh_loop():
        import time
        while not state["stop"].is_set():
            snap = build_snapshot()
            state["snapshot"] = snap
            if icon is not None:
                icon.title = f"Qoder usage\n{tooltip(snap)}"
                icon.icon = _make_image(snap.latest_context_ratio())
            state["stop"].wait(interval)

    def on_quit(_item):
        state["stop"].set()
        icon.stop()

    def on_details(_item):
        snap = state["snapshot"]
        if snap:
            print(tooltip(snap))

    menu = pystray.Menu(
        pystray.MenuItem("Details", on_details),
        pystray.MenuItem("Quit", on_quit),
    )
    icon = pystray.Icon("qoder-usage", menu=menu,
                        title="Qoder usage",
                        icon=_make_image(0.0))

    threading.Thread(target=refresh_loop, daemon=True).start()
    icon.run(detach=True) if _is_mac() else icon.run()
    state["stop"].set()
    return 0


def _is_mac() -> bool:
    import sys
    return sys.platform == "darwin"
