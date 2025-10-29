from aqt import mw
from aqt.utils import showWarning
from aqt.qt import *
from .base_dialog import BaseBackfillDialog
from . import yomitan_api  

class ToolsBackfill:
    def __init__(self):
        action = QAction("Backfill from Yomitan", mw)
        action.triggered.connect(self._open_dialog)
        mw.form.menuTools.addAction(action)

    def _open_dialog(self):
        if not yomitan_api.ping_yomitan():
            showWarning('Unable to reach Yomitan API')
            return
        
        dlg = self.ToolsDialog(mw)
        dlg.resize(350, dlg.height())
        if hasattr(dlg, "exec_"):
            # qt5
            dlg.exec_()
        else:
            # qt6
            dlg.exec()

    class ToolsDialog(BaseBackfillDialog):
        def __init__(self, parent):
            super().__init__(parent)

            self.decks = QComboBox()
            self.form.insertRow(0, QLabel("Deck:"), self.decks)

            self._load_decks()
            self._update_fields()
            
            self.decks.currentIndexChanged.connect(self._update_fields)

        def _load_decks(self):
            self.decks.clear()
            decks = mw.col.decks.all()
            for deck in decks:
                name = deck.get("name")
                deck_id = deck.get("id")
                self.decks.addItem(name, deck_id)

        def _get_note_ids(self):
            return mw.col.db.list("SELECT DISTINCT nid FROM cards WHERE did = ?", self._get_deck_id())
        
        def _get_deck_name(self):
            return self.decks.currentText()
        
        def _get_deck_id(self):
            return self.decks.currentData()
        
