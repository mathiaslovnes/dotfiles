"""Per-note-type field settings. Extra note types live in the add-on config under
"extra_note_types" (list of {note_type, word_field, sentence_field, explanation_field,
explanation_audio_field}); missing keys fall back to the main settings."""

from __future__ import annotations

from .config import CONFIG


def profile_for(model_name: str):
    if model_name == CONFIG.get("note_type"):
        return CONFIG
    for profile in CONFIG.get("extra_note_types") or []:
        if isinstance(profile, dict) and profile.get("note_type") == model_name:
            return profile
    return None


def fcfg(note, key: str) -> str:
    profile = profile_for(note.note_type()["name"]) or CONFIG
    return profile.get(key) or CONFIG.get(key, "")
