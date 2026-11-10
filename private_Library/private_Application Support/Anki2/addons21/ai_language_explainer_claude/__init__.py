"""Entry point for the AI Language Explainer add-on."""

from __future__ import annotations

import traceback

from aqt import gui_hooks

from .alx.config import (
    CONFIG,
    get_fields_for_note_type,
    get_note_types,
    load_config,
    save_config,
    set_addon_module_name,
)
from .alx.dependencies import check_dependencies
from .alx.logging import debug_log, setup_crash_handler
from .alx.menu import batch_process_notes, open_settings, setup_menu
from .alx.processing import process_note, process_note_debug
from .alx.reviewer import (
    add_button_to_reviewer,
    on_card_shown,
    on_js_message,
    process_current_card,
)
from .alx.ui.bulk_dialog import BulkGenerationDialog
from .alx.ui.config_dialog import ConfigDialog


setup_crash_handler()
check_dependencies()
set_addon_module_name(__name__)


def _card_template_has(marker: str) -> bool:
    from aqt import mw
    card = mw.reviewer.card if mw.reviewer else None
    if not card:
        return False
    nt = card.note_type()
    tmpl = nt["tmpls"][card.ord] if nt["type"] == 0 else nt["tmpls"][0]
    side = tmpl.get("qfmt", "")
    if mw.reviewer.state == "answer":
        side += tmpl.get("afmt", "")
    return marker in side


def _card_key(name: str, fallback=None) -> None:
    import json
    from aqt import mw
    if mw.state != "review" or not mw.reviewer.card:
        return
    if _card_template_has("_cardKey"):
        mw.reviewer.web.eval(f"window._cardKey && window._cardKey({json.dumps(name)});")
    elif fallback:
        fallback()


def _note_has(field_key: str, default: str = "") -> bool:
    from aqt import mw
    from .alx.profiles import fcfg, profile_for
    card = mw.reviewer.card if mw.state == "review" else None
    if not card:
        return False
    note = card.note()
    if profile_for(note.note_type()["name"]) is None:
        return False
    f = fcfg(note, field_key) or default
    return bool(f) and f in note and bool(note[f].strip())


def _g_key() -> None:
    """g: show/hide the explanation in the 解説 panel; generate it right away if there is
    none. Shift+G always opens the generate dialog (to regenerate: it replaces the old one)."""
    from aqt import mw
    if mw.state != "review" or not mw.reviewer.card or mw.reviewer.state != "answer":
        return
    if _note_has("explanation_field"):
        from .alx.panel import panel
        panel("exp")
    else:
        process_current_card(confirm=False)


def _c_key() -> None:
    """c: show/hide the contrast in the 解説 panel; make one (pick the words first) if
    there is none. Shift+C always makes a new one."""
    from aqt import mw
    if mw.state != "review" or not mw.reviewer.card or mw.reviewer.state != "answer":
        return
    if _note_has("contrast_field", "contrast"):
        from .alx.panel import panel
        panel("con")
    else:
        from .alx.contrast import start_contrast
        start_contrast()


def _answer_side() -> bool:
    from aqt import mw
    return mw.state == "review" and bool(mw.reviewer.card) and mw.reviewer.state == "answer"


def _contrast_regen_key() -> None:
    if _answer_side():
        from .alx.contrast import start_contrast
        start_contrast()


def _regen_explanation_key() -> None:
    if _answer_side():
        process_current_card()


def _explain_audio_key() -> None:
    """Cmd+R: show the explanation and play its audio."""
    if _answer_side():
        from .alx.panel import panel
        panel("exp", "show")
        _card_key("explain")


def _add_card_keys(state, shortcuts) -> None:
    if state != "review":
        return
    from aqt import mw
    shortcuts.extend([
        ("Ctrl+R", _explain_audio_key),  # Qt's Ctrl = Cmd on macOS
        ("g", _g_key),
        ("Shift+G", _regen_explanation_key),
        ("c", _c_key),
        ("Shift+C", _contrast_regen_key),
    ])


def init() -> None:
    try:
        debug_log("Initializing AI Language Explainer addon")

        load_config()
        debug_log(f"Configuration loaded: {CONFIG}")

        setup_menu()
        debug_log("Menu setup complete")

        debug_log("Registering hooks")
        gui_hooks.reviewer_did_show_answer.append(on_card_shown)
        debug_log("Registered reviewer_did_show_answer hook")
        gui_hooks.webview_did_receive_js_message.append(on_js_message)
        debug_log("Registered webview_did_receive_js_message hook")
        gui_hooks.state_shortcuts_will_change.append(_add_card_keys)
        from anki import hooks as anki_hooks
        from .alx.auto import on_note_will_be_added
        anki_hooks.note_will_be_added.append(on_note_will_be_added)
        from .alx.contrast import add_remove_buttons, on_js_message as contrast_js_message
        gui_hooks.webview_did_receive_js_message.append(contrast_js_message)
        gui_hooks.card_will_show.append(add_remove_buttons)

        debug_log("AI Language Explainer addon initialization complete")
    except Exception as err:
        debug_log(f"Error during initialization: {err}")
        debug_log(traceback.format_exc())


init()


__all__ = [
    "CONFIG",
    "BulkGenerationDialog",
    "ConfigDialog",
    "add_button_to_reviewer",
    "batch_process_notes",
    "debug_log",
    "get_fields_for_note_type",
    "get_note_types",
    "load_config",
    "open_settings",
    "process_current_card",
    "process_note",
    "process_note_debug",
    "save_config",
    "setup_menu",
]
