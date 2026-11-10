"""New Card Position Guard: new cards are shown in the order they were added.

Anki shows new cards by their queue number (position), and gives a new card its number from
a counter. On this collection something sets that counter back now and then, so cards mined
on different days got the same numbers and were shown mixed together.

Right before a note is added (Add window, Yomitan / AnkiConnect, anything that goes through
Anki's add_note / add_notes), this looks up the highest number any new card has and makes the
new card's number one higher. So the newest card is always last, and the order of new cards is
the order they were added. Each time the counter was behind, that is written to
user_files/log.txt, so the log shows when it gets set back."""

import os
import time

from anki import hooks

LOG = os.path.join(os.path.dirname(__file__), "user_files", "log.txt")


def _log(text: str) -> None:
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + text + "\n")
    except OSError:
        pass


def _before_add(col, note, deck_id) -> None:
    try:
        top = col.db.scalar("select max(due) from cards where type = 0") or 0
        nxt = int(col.get_config("nextPos", 0) or 0)
        if nxt <= top:
            col.set_config("nextPos", top + 1)
            _log(f"next position was {nxt}, highest new card {top}; set to {top + 1}")
    except Exception as e:
        _log(f"check failed: {e!r}")


hooks.note_will_be_added.append(_before_add)
