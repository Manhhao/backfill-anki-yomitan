from aqt import gui_hooks, mw
from aqt.browser import Browser
from aqt.utils import showWarning
from aqt.qt import *
from .base_dialog import BaseBackfillDialog
from . import yomitan_api

class BrowserBackfill:
    def __init__(self):
        gui_hooks.browser_menus_did_init.append(self._add_to_browser)

    def _open_browser_dialog(self, browser: Browser):
        if not yomitan_api.ping_yomitan():
            showWarning('Unable to reach Yomitan API<br><a href="https://github.com/Manhhao/backfill-anki-yomitan?tab=readme-ov-file#issues">Check if you need to update your API</a>')
            return
        
        selected_note_ids = list(browser.selectedNotes())
        if not selected_note_ids:
            showWarning("No notes selected")
            return

        dlg = self.BrowserDialog(browser, selected_note_ids)
        dlg.resize(350, dlg.height())

        if hasattr(dlg, "exec_"):
            # qt5
            dlg.exec_()
        else:
            # qt6
            dlg.exec()

    def _add_to_browser(self, browser: Browser):
        action = QAction("Backfill from Yomitan", browser)
        action.triggered.connect(lambda: self._open_browser_dialog(browser))
        browser.form.menuEdit.addAction(action)
    
    class BrowserDialog(BaseBackfillDialog):
        def __init__(self, parent, selected_note_ids):
            super().__init__(parent)

            self.note_ids = selected_note_ids
            note = mw.col.get_note(self.note_ids[0])
            card = note.cards()[0]

            self.deck_id = card.did
            self.deck_name = mw.col.decks.name(self.deck_id)

            self.decks = QLineEdit()
            self.decks.setText(self.deck_name)
            self.decks.setReadOnly(True)
            self.form.insertRow(0, QLabel("Deck:"), self.decks)

            self._update_fields()

        def _get_note_ids(self):
            return self.note_ids
        
        def _get_deck_name(self):
            return self.deck_name
        
        def _get_deck_id(self):
            return self.deck_id
        