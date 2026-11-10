"""Show parts of the 解説 panel from the keyboard: the explanation (g) and the
contrast (c) can be shown on their own or together; the title stays 解説.

The template marks what the note has (has-exp / has-con on #llmDefinition) and
CSS hides a part when the panel has hide-exp / hide-con. Clicking the 解説 pill
still opens everything."""

from __future__ import annotations

import json

from aqt import mw

_JS = """(function (part, mode) {
  var d = document.getElementById('llmDefinition');
  if (!d) return;
  if (!d._alx) {           // closing the panel, by click or key, resets it to "show all"
    d._alx = 1;
    d.addEventListener('toggle', function () { if (!d.open) d.classList.remove('hide-exp', 'hide-con'); });
  }
  var other = part === 'exp' ? 'con' : 'exp';
  var hasOther = d.classList.contains('has-' + other);
  if (!d.open) {                                   // closed: open with only this part
    d.classList.remove('hide-' + part);
    d.classList.toggle('hide-' + other, hasOther);
    d.open = true;
    return;
  }
  if (d.classList.contains('hide-' + part)) {      // open without it: add it
    d.classList.remove('hide-' + part);
    return;
  }
  if (mode === 'show') return;
  if (!hasOther || d.classList.contains('hide-' + other)) { d.open = false; return; }
  d.classList.add('hide-' + part);                 // both shown: hide this one
})(%s, %s);"""


def panel(part: str, mode: str = "toggle") -> None:
    """part: "exp" or "con"; mode: "toggle" or "show"."""
    if mw.state != "review" or not mw.reviewer.card or mw.reviewer.state != "answer":
        return
    mw.reviewer.web.eval(_JS % (json.dumps(part), json.dumps(mode)))


_VISIBLE_JS = """(function (part) {
  var d = document.getElementById('llmDefinition');
  if (!d) return false;
  d._stale = 1;                     // the redraw replaces this element
  return d.open && !d.classList.contains('hide-' + part);
})(%s)"""

_REVEAL_JS = """(function (part, keepOther) {
  var tries = 0;
  (function go() {
    var d = document.getElementById('llmDefinition');
    if (!d || d._stale) { if (tries++ < 60) setTimeout(go, 50); return; }   // wait for the redraw
    if (!d._alx) {
      d._alx = 1;
      d.addEventListener('toggle', function () { if (!d.open) d.classList.remove('hide-exp', 'hide-con'); });
    }
    var other = part === 'exp' ? 'con' : 'exp';
    d.classList.remove('hide-' + part);
    d.classList.toggle('hide-' + other, !keepOther && d.classList.contains('has-' + other));
    d.open = true;
  })();
})(%s, %s);"""


def redraw_and_reveal(part: str) -> None:
    """Redraw the card after `part` ("exp"/"con") was generated and open the panel on it.
    The other part stays visible only if it was visible before."""
    if mw.state != "review" or not mw.reviewer.card:
        return
    if mw.reviewer.state != "answer":
        mw.reviewer._redraw_current_card()
        return
    other = "con" if part == "exp" else "exp"
    nid = mw.reviewer.card.nid

    def redraw(other_visible) -> None:
        if mw.state != "review" or not mw.reviewer.card or mw.reviewer.card.nid != nid:
            return
        mw.reviewer._redraw_current_card()
        mw.reviewer.web.eval(_REVEAL_JS % (json.dumps(part), json.dumps(bool(other_visible))))

    mw.reviewer.web.evalWithCallback(_VISIBLE_JS % json.dumps(other), redraw)


__all__ = ["panel", "redraw_and_reveal"]
