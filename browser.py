from aqt import gui_hooks, mw
from aqt.browser import Browser
from aqt.operations import CollectionOp
from aqt.utils import showWarning
from aqt.qt import *
from . import anki_util
from . import logger
from . import yomitan_api
import json

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
    
    class BrowserDialog(QDialog):
        def __init__(self, parent, selected_note_ids):
            super().__init__(parent)
            self.setWindowTitle("Yomitan Backfill")
            self.note_ids = selected_note_ids

            note = mw.col.get_note(self.note_ids[0])
            card = note.cards()[0]
            self.deck_id = card.did

            self.decks = QLineEdit()
            self.fields = QComboBox()
            self.expression_field = QComboBox()
            self.reading_field = QComboBox()
            self.yomitan_handlebars = QLineEdit()
            self.apply = QPushButton("Run")
            self.cancel = QPushButton("Cancel")
            self.replace = QCheckBox("Replace")
            self.tab_widget = QTabWidget()

            # single field widgets
            self.single_tab = QWidget()
            self.fields = QComboBox()
            self.yomitan_handlebars = QLineEdit()

            # preset widgets
            self.json_tab = QWidget()
            self.preset = QComboBox()
            self.open_folder = QPushButton("Open Folder")
            
            deck_name = mw.col.decks.name(self.deck_id)
            self.decks.setText(deck_name)
            self.decks.setReadOnly(True)

            form = QFormLayout()
            form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
            form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
            form.addRow(QLabel("Deck:"), self.decks)
            form.addRow(QLabel("Expression Field:"), self.expression_field)
            form.addRow(QLabel("Reading Field:"), self.reading_field)

            # single field layout
            form_single_tab = QFormLayout()
            form_single_tab.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
            form_single_tab.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
            form_single_tab.addRow(QLabel("Field:"), self.fields)
            form_single_tab.addRow(QLabel("Handlebar:"), self.yomitan_handlebars)
            form_single_tab.addRow(self.replace)
            self.single_tab.setLayout(form_single_tab)

            # preset layout
            form_json_tab = QFormLayout()
            form_json_tab.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
            form_json_tab.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
            form_json_tab.addRow(QLabel("Preset"), self.preset)
            format_hyperlink = QLabel('<a href="https://github.com/Manhhao/backfill-anki-yomitan?tab=readme-ov-file#presets">Preset Format</a>')
            format_hyperlink.setOpenExternalLinks(True)
            form_json_tab.addRow(format_hyperlink)
            form_json_tab.addRow(self.open_folder)
            self.json_tab.setLayout(form_json_tab)

            self.tab_widget.addTab(self.single_tab, "Single Field")
            self.tab_widget.addTab(self.json_tab, "Presets")

            buttons = QHBoxLayout()
            buttons.addWidget(self.apply)
            buttons.addWidget(self.cancel)

            tabs = QHBoxLayout()
            tabs.addWidget(self.tab_widget)

            layout = QVBoxLayout()
            layout.addLayout(form)
            layout.addLayout(tabs)
            layout.addLayout(buttons)
            self.setLayout(layout)
            
            self._update_fields()
            self._load_presets()

            self.apply.clicked.connect(self._on_run)
            self.cancel.clicked.connect(self.reject)
            self.open_folder.clicked.connect(anki_util.open_user_files_folder)

        def _update_fields(self):
            self.fields.clear()
            self.expression_field.clear()
            self.reading_field.clear()

            if self.deck_id is None:
                return

            model_ids = mw.col.db.list("SELECT DISTINCT n.mid FROM notes n JOIN cards c ON n.id = c.nid WHERE c.did = ?", self.deck_id)

            field_names = set()
            for mid in model_ids:
                model = mw.col.models.get(mid)
                for fld in model.get('flds', []):
                    field_names.add(fld.get('name'))

            for name in sorted(field_names):
                self.fields.addItem(name)
                self.expression_field.addItem(name)
                self.reading_field.addItem(name)

            self.reading_field.setCurrentIndex(-1)

        def _load_presets(self):
            self.preset.clear()
            self.preset.addItems(anki_util.read_user_files_folder())

        def _on_run(self):
            logger.log.info(f"started browser backfill on {self.decks.currentData}")
            if self.tab_widget.currentIndex() == 0:
                self._run_single_field()
            else:
                self._run_preset()
                
        def _run_single_field(self):
            expression_field = self.expression_field.currentText()
            reading_field = self.reading_field.currentText()
            field = self.fields.currentText()
            handlebars = [p.lstrip("{").rstrip("}") for p in self.yomitan_handlebars.text().split(",") if p.strip()]
            should_replace = self.replace.isChecked()

            op = CollectionOp(
                parent = mw,
                op = lambda col: anki_util.backfill_notes(col, self.note_ids, expression_field, reading_field, handlebars, [(field, handlebars, should_replace)])
            )
            
            op.success(anki_util.on_success).run_in_background()

        def _run_preset(self):
            expression_field = self.expression_field.currentText()
            reading_field = self.reading_field.currentText()
            handlebars = []
            target_tuples = []

            try:
                path = os.path.join(anki_util.get_user_files_dir(), self.preset.currentText())
                with open(path) as f:
                    preset = json.load(f)
                    targets = preset.get("targets")
                    for field, settings in targets.items():
                        handlebar = [p.lstrip("{").rstrip("}") for p in settings.get("handlebar").split(",") if p.strip()]
                        should_replace = settings.get("replace")
                        handlebars.extend(handlebar)
                        target_tuples.append((field, handlebar, should_replace))
            except json.JSONDecodeError as e:
                logger.log.error(e.msg)
                showWarning("The selected .json file contains errors.<br>Check the log for more information.")
                return
            except AttributeError as e:
                logger.log.error(e.msg)
                showWarning("One or more Field(s) are missing keys (handlebar or replace).")
                return
            except Exception as e:
                logger.log.error(e.msg)
                return

            op = CollectionOp(
                parent = mw,
                op = lambda col: anki_util.backfill_notes(col, self.note_ids, expression_field, reading_field, handlebars, target_tuples)
            )
            
            op.success(anki_util.on_success).run_in_background()