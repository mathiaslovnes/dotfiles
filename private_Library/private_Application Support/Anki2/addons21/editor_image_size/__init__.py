"""Editor Image Size: how big pictures are in the editor while "Shrink images"
(⚙ in the editor toolbar) is on. Anki's own cap is 250 x 125 px; this sets it
from the add-on's config (max_width / max_height, in px)."""

from aqt import gui_hooks, mw
from aqt.editor import Editor


def _style() -> str:
    cfg = mw.addonManager.getConfig(__name__) or {}
    w, h = int(cfg.get("max_width", 300)), int(cfg.get("max_height", 150))
    sizes = "".join(f"--editor-{kind}-max-width:{w}px!important;--editor-{kind}-max-height:{h}px!important;"
                    for kind in ("default", "shrink"))
    return f"<style>:root{{{sizes}}}</style>"


def _on_content(web_content, context) -> None:
    if isinstance(context, Editor):
        web_content.head += _style()


gui_hooks.webview_will_set_content.append(_on_content)
