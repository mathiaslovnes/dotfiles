"""Card keys: r and Shift+R go to the card's own window._cardKey("r" / "R") when its
template defines one (e.g. r = word audio, Shift+R = sentence audio), instead of
Anki's replay, which plays every sound on the card. Cards without _cardKey keep
Anki's normal r. Window-level shortcuts are used because the card itself often
doesn't receive key presses (Anki's own shortcuts take them first)."""

from __future__ import annotations

import json

from aqt import gui_hooks, mw


def _template_has(marker: str) -> bool:
    card = mw.reviewer.card if mw.reviewer else None
    if not card:
        return False
    nt = card.note_type()
    tmpl = nt["tmpls"][card.ord] if nt["type"] == 0 else nt["tmpls"][0]
    # on the front only the front template counts (window._cardKey may still be
    # the previous card's)
    side = tmpl.get("qfmt", "")
    if mw.reviewer.state == "answer":
        side += tmpl.get("afmt", "")
    return marker in side


def card_key(name: str, fallback=None) -> None:
    if mw.state != "review" or not mw.reviewer.card:
        return
    if _template_has("_cardKey"):
        mw.reviewer.web.eval(f"window._cardKey && window._cardKey({json.dumps(name)});")
    elif fallback:
        fallback()


def _shortcuts(state, shortcuts) -> None:
    if state != "review":
        return
    shortcuts[:] = [s for s in shortcuts if not (isinstance(s[0], str) and s[0] == "r")]
    shortcuts.extend([
        ("r", lambda: card_key("r", mw.reviewer.replayAudio)),
        ("Shift+R", lambda: card_key("R")),
    ])


def setup() -> None:
    gui_hooks.state_shortcuts_will_change.append(_shortcuts)


setup()
