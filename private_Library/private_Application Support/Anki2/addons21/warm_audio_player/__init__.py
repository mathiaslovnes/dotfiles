"""Play card audio without the start-up delay or clicks

Anki plays sound through a hidden copy of mpv, started with --gapless-audio=no, so mpv closes the
Mac's audio output after every sound and opens it again for the next one. Two problems came from
that:

1. Delay: after more than about a second of quiet, the output takes 250-350 ms to start
   (measured with AirPods), so the word audio came late when a card was flipped.
2. Clicks: with YouTube or Music playing at the same time, the output closing and reopening
   clicks. Each card sound cost two of them, one at its start and one at its end.

While you review, this keeps one audio output open the whole time:
- mpv plays silence whenever no card audio is playing;
- output is fixed at 48 kHz stereo float with gapless audio on, so a card's sound replaces the
  silence on the open output whatever its own format (mono files are copied to both sides at
  full level; mpv's own mono-to-stereo step would make them 3 dB quieter);
- silence is queued behind each card sound, so the end of the sound doesn't close the output.
  mpv then never goes idle, which is how Anki normally learns a sound has ended, so this tells
  Anki itself when the queued silence starts;
- Anki's stop (replay, flipping during a sound) loads silence instead of stopping mpv.
Leaving the review screen stops the silence. Outside review, Anki's player works as before."""
from aqt import gui_hooks, mw
from aqt.sound import MpvManager, av_player

from .channels import is_mono

_PREFIX = "av://lavfi:anullsrc=r=48000:cl=stereo"
_FIXED = (
    ("gapless-audio", "yes"),
    ("audio-samplerate", 48000),
    ("audio-channels", "stereo"),
    ("audio-format", "float"),
    ("audio-stream-silence", "yes"),  # pausing keeps the output open too
)
_MONO_AF = "lavfi=[pan=stereo|c0=c0|c1=c0]"
_end_marker = None  # the silence queued behind the card sound that is playing
_count = 0
_af = None  # the af last set, to skip needless changes


def _silence(n: int = 0) -> str:
    """Numbered, so each card sound's end shows up as a change of mpv's path."""
    return f"{_PREFIX}:n={1024 + n},aformat=sample_fmts=flt"


def _player():
    return next((p for p in av_player.players if isinstance(p, MpvManager)), None)


def _reviewing() -> bool:
    return mw.state == "review"


def _playing_silence(p) -> bool:
    try:
        return str(p.get_property("path") or "").startswith(_PREFIX)
    except Exception:
        return False


def _take_done(p) -> None:
    """Tell Anki the card sound ended, once: clearing _on_done keeps Anki's own idle handler
    from sending it a second time."""
    cb, p._on_done = p._on_done, None
    if cb:
        mw.taskman.run_on_main(cb)


def _set_af(p, af: str) -> None:
    global _af
    if af != _af:
        p.set_property("af", af)
        _af = af


def _warm() -> None:
    p = _player()
    if p is None or not _reviewing() or av_player.current_player is not None:
        return  # not reviewing, or Anki is playing something
    try:
        if p.get_property("idle-active"):
            p._on_done = None  # the finished sound's callback has already been queued
            p.command("loadfile", _silence(), "replace")
    except Exception:
        pass


def _cool() -> None:
    p = _player()
    if p is None or _reviewing() or not _playing_silence(p):
        return
    try:
        p.command("stop")
    except Exception:
        pass


def _on_idle(value: bool) -> None:
    # Runs after Anki's own idle handler, which has queued "sound finished" (mpv only goes idle
    # here when this add-on didn't queue silence, e.g. outside review or after a mpv restart).
    if value:
        mw.taskman.run_on_main(_warm)


def _on_path(value) -> None:
    # mpv's event thread: the silence queued behind a card sound has started, so the sound ended
    global _end_marker
    if value is not None and value == _end_marker:
        _end_marker = None
        p = _player()
        if p is not None:
            _take_done(p)
        mw.taskman.run_on_main(_cool)  # in case review was left while the sound played


def _patch(p) -> None:
    if getattr(p, "_warm_patched", False):
        return
    orig_play, orig_stop = p.play, p.stop

    def play(tag, on_done):
        global _end_marker, _count
        try:
            _set_af(p, _MONO_AF if is_mono(tag.path(p.media_folder)) else "")
        except Exception:
            pass
        orig_play(tag, on_done)
        if not _reviewing():
            return
        _count = _count % 999 + 1
        _end_marker = _silence(_count)
        try:
            p.command("loadfile", _end_marker, "append")
        except Exception:
            _end_marker = None

    def stop():
        global _end_marker
        if not _reviewing():
            return orig_stop()
        _end_marker = None
        cb, p._on_done = p._on_done, None
        try:
            p.command("loadfile", _silence(), "replace")
        except Exception:
            p._on_done = cb
            return orig_stop()
        if cb:
            mw.taskman.run_on_main(cb)

    p.play, p.stop = play, stop
    p._warm_patched = True


def _ensure_hook() -> None:
    """Anki's player is created and wired up before add-ons load, and mpv restarts drop
    callbacks and settings, so check them each time a question is shown. Anki already observes
    idle-active, so no second observe for it (that would call Anki's own handler twice)."""
    global _af
    p = _player()
    if p is None:
        return
    _patch(p)
    callbacks = p._callbacks.setdefault("property-idle-active", [])
    if _on_idle not in callbacks:
        callbacks.append(_on_idle)
    try:
        if _on_path not in p._callbacks.get("property-path", []):
            p.register_property_callback("path", _on_path)
        if p.get_property("gapless-audio") not in (True, "yes"):
            for name, value in _FIXED:
                p.set_property(name, value)
            _af = None
    except Exception:
        pass


def _on_state(new_state, old_state) -> None:
    _ensure_hook()
    if new_state == "review":
        _warm()
    else:
        _cool()


def _before_state(new_state, old_state) -> None:
    # before the reviewer shows its first card, so even that card's sound uses the open output
    if new_state == "review":
        _ensure_hook()
        _warm()


gui_hooks.state_will_change.append(_before_state)
gui_hooks.state_did_change.append(_on_state)
gui_hooks.reviewer_did_show_question.append(lambda card: (_ensure_hook(), _warm()))
