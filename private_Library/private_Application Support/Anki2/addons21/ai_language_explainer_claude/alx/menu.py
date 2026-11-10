"""Menus and batch processing entry points."""

from __future__ import annotations

import threading
import traceback

from aqt import gui_hooks, mw
from aqt.browser import Browser
from aqt.qt import QAction, QDialog, QKeySequence, QMenu, QMessageBox, QProgressDialog, QShortcut, Qt
from aqt.utils import qconnect, showInfo, tooltip

from .config import CONFIG
from .contrast import contrast_notes, notify_note_changed
from .profiles import fcfg, profile_for
from .logging import debug_log
from .processing import process_note
from .ui.bulk_dialog import BulkGenerationDialog
from .ui.config_dialog import ConfigDialog
from .ui.error_dialog import ErrorDetailsDialog


def setup_menu():
    # Create main menu for AI Language Explainer
    ai_explainer_menu = QMenu("AI Language Explainer", mw)
    
    # Add settings as a submenu option
    settings_action = QAction("Settings", mw)
    qconnect(settings_action.triggered, open_settings)
    ai_explainer_menu.addAction(settings_action)
    
    # Add the menu to the Tools menu
    mw.form.menuTools.addMenu(ai_explainer_menu)
    
    # Enable browser menu action for bulk processing
    debug_log("Registering browser_menus_did_init hook for batch processing")
    gui_hooks.browser_menus_did_init.append(setup_browser_menu)
    gui_hooks.browser_will_show_context_menu.append(add_to_context_menu)
    debug_log("Browser hook registered")


def open_settings():
    dialog = ConfigDialog(mw)
    dialog.exec()


def batch_process_notes(browser=None):
    browser = browser or mw.app.activeWindow()
    if not isinstance(browser, Browser):
        showInfo("Please open this from the Browser view")
        return
    
    # Get selected note ids
    selected_notes = browser.selectedNotes()
    if not selected_notes:
        showInfo("No cards selected. Please select cards to process.")
        return
    
    # Check if configuration is loaded
    if not CONFIG["api_key"]:
        showInfo("Please set your Claude API key in the AI Language Explainer Settings.")
        return
    
    # Show the bulk generation options dialog with selected notes for analysis
    bulk_dialog = BulkGenerationDialog(browser, selected_notes)
    if bulk_dialog.exec() != QDialog.DialogCode.Accepted:
        debug_log("User canceled bulk generation dialog")
        return
    
    # Get the generation options from the dialog (4 values: generate_text, generate_audio, override_text, override_audio)
    generate_text, generate_audio, override_text, override_audio = bulk_dialog.get_generation_options()
    debug_log(f"Bulk generation options: generate_text={generate_text}, generate_audio={generate_audio}, override_text={override_text}, override_audio={override_audio}")
    
    # Store generation flags for backend processing
    CONFIG["generate_text"] = generate_text
    CONFIG["generate_audio"] = generate_audio
    CONFIG["override_text"] = override_text
    CONFIG["override_audio"] = override_audio
    
    # Create a progress dialog with fixed width to avoid the resizing issue
    progress = QProgressDialog("Processing cards...", "Cancel", 0, len(selected_notes) + 1, browser)
    progress.setWindowTitle("AI Language Explainer Batch Processing")
    
    # Fix for Qt6 compatibility - use Qt.WindowModality.ApplicationModal instead of Qt.WindowModal
    try:
        # Try Qt6 style enum first
        progress.setWindowModality(Qt.WindowModality.ApplicationModal) 
    except AttributeError:
        # Fallback to Qt5 style for backwards compatibility
        try:
            progress.setWindowModality(Qt.ApplicationModal)
        except:
            # Last resort fallback - don't set modality if both approaches fail
            debug_log("Failed to set window modality - Qt version compatibility issue")
            
    progress.setMinimumWidth(400)  # Set fixed width to avoid resizing issue
    progress.setValue(0)
    progress.show()
    
    # Process notes in a separate thread to keep UI responsive
    def process_notes_thread():
        success_count = 0
        skipped_count = 0
        error_count = 0
        missing_fields_count = 0
        errors = {}  # Dict[note_id] -> (card_info, error_message)

        try:
            for i, note_id in enumerate(selected_notes):
                if progress.wasCanceled():
                    break

                note = mw.col.get_note(note_id)

                # Update progress UI from main thread
                mw.taskman.run_on_main(lambda i=i, total=len(selected_notes):
                    progress.setLabelText(f"Processing card {i+1} of {total}..."))
                mw.taskman.run_on_main(lambda i=i: progress.setValue(i+1))

                # Skip processing if note type doesn't match configured type
                model_name = note.note_type()["name"]
                if profile_for(model_name) is None:
                    debug_log(f"Skipping note {note_id}: Note type {model_name} doesn't match configured type {CONFIG['note_type']}")
                    missing_fields_count += 1
                    continue

                # Skip processing if required fields are missing
                required_fields = [fcfg(note, "word_field"), fcfg(note, "sentence_field")]
                if not all(field in note and field in note.keys() for field in required_fields):
                    debug_log(f"Skipping note {note_id}: Missing required fields")
                    missing_fields_count += 1
                    continue

                # Extract card info for error reporting
                card_info = "Unknown"
                try:
                    if fcfg(note, "word_field") in note:
                        word = note[fcfg(note, "word_field")]
                        # Truncate if too long
                        card_info = word[:50] + "..." if len(word) > 50 else word
                except Exception:
                    pass

                # Process the note with separate generation flags
                success, message = process_note(note, generate_text, generate_audio, override_text, override_audio, progress_callback=None)
                if success:
                    # Check for different skip messages that were updated
                    if "already exists" in message or "not requested" in message:
                        skipped_count += 1
                        debug_log(f"Note {note_id} skipped: {message}")
                    else:
                        success_count += 1
                        debug_log(f"Note {note_id} processed successfully: {message}")
                        # Save changes to the database
                        note.col.update_note(note)
                else:
                    error_count += 1
                    errors[note_id] = (card_info, message)
                    debug_log(f"Note {note_id} failed: {message}")
            
            # Final update on main thread
            mw.taskman.run_on_main(lambda: progress.setValue(len(selected_notes) + 1))

            # Show results
            def show_results():
                notify_note_changed()        # the Browser's editor reloads the note
                if errors:
                    # Show detailed error dialog
                    error_dialog = ErrorDetailsDialog(
                        parent=browser,
                        errors=errors,
                        success_count=success_count,
                        skipped_count=skipped_count,
                        missing_fields_count=missing_fields_count,
                    )
                    error_dialog.exec()
                else:
                    msg = f"Explanation generated for {success_count} note{'s' if success_count != 1 else ''}"
                    if skipped_count or missing_fields_count:
                        msg += f" ({skipped_count + missing_fields_count} skipped)"
                    tooltip(msg, parent=browser)

            mw.taskman.run_on_main(show_results)
            
        except Exception as e:
            debug_log(f"Error in batch processing: {str(e)}")
            debug_log(traceback.format_exc())
            mw.taskman.run_on_main(lambda: 
                showInfo(f"Error in batch processing: {str(e)}"))
        finally:
            mw.taskman.run_on_main(lambda: progress.hide())
    
    # Start processing thread
    threading.Thread(target=process_notes_thread, daemon=True).start()


# Browser shortcuts (Ctrl is Cmd on macOS). They only work while the card list has focus, so
# in a text field (editor, search) Cmd+X / Cmd+C still cut and copy.
EXPLAIN_SHORTCUT, CONTRAST_SHORTCUT = "Ctrl+X", "Ctrl+C"


def setup_browser_menu(browser):
    """Edit menu and right-click menu: generate the explanation or the contrast for the
    selected notes."""
    explain = QAction("Generate explanation (解説)", browser)
    qconnect(explain.triggered, lambda: batch_process_notes(browser))
    contrast = QAction("Generate contrast (使い分け)", browser)
    qconnect(contrast.triggered, lambda: _contrast_selected(browser))
    browser._alx_actions = (explain, contrast)
    menu = getattr(browser.form, "menuEdit", None) or browser.form.menuTools
    menu.addSeparator()
    menu.addAction(explain)
    menu.addAction(contrast)
    view = getattr(browser.form, "tableView", None)
    if view is not None:
        for keys, action in ((EXPLAIN_SHORTCUT, explain), (CONTRAST_SHORTCUT, contrast)):
            shortcut = QShortcut(QKeySequence(keys), view)
            shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
            qconnect(shortcut.activated, action.trigger)


def _contrast_selected(browser) -> None:
    nids = browser.selectedNotes()
    if not nids:
        tooltip("No cards selected.", parent=browser)
        return
    contrast_notes(nids, parent=browser)


def add_to_context_menu(browser, menu) -> None:
    actions = getattr(browser, "_alx_actions", None)
    if actions:
        menu.addSeparator()
        for action in actions:
            menu.addAction(action)


__all__ = [
    "setup_menu",
    "open_settings",
    "batch_process_notes",
    "setup_browser_menu",
]
