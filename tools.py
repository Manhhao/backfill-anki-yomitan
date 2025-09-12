from aqt import mw
from aqt.operations import CollectionOp
from aqt.utils import showWarning
from aqt.qt import *
from . import anki_util  
from . import logger
from . import yomitan_api  
import json

class ToolsBackfill:
    def __init__(self):
        action = QAction("Backfill from Yomitan", mw)
        action.triggered.connect(self._open_dialog)
        mw.form.menuTools.addAction(action)

    def _open_dialog(self):
        if not yomitan_api.ping_yomitan():
            showWarning('Unable to reach Yomitan API<br><a href="https://github.com/Manhhao/backfill-anki-yomitan?tab=readme-ov-file#issues">Check if you need to update your API</a>')
            return
        
        dlg = self.ToolsDialog(mw)
        dlg.resize(350, dlg.height())
        if hasattr(dlg, "exec_"):
            # qt5
            dlg.exec_()
        else:
            # qt6
            dlg.exec()

    class ToolsDialog(QDialog):
        def __init__(self, parent):
            super().__init__(parent)
            logger.setup_logging()
            self.finished.connect(lambda: logger.shutdown_logging())
            self.setWindowTitle("Yomitan Backfill")

            self.decks = QComboBox()
            self.expression_field = QComboBox()
            self.reading_field = QComboBox()
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

            self._load_decks()
            self._update_fields()
            self._load_presets()

            self.decks.currentIndexChanged.connect(self._update_fields)
            self.apply.clicked.connect(self._on_run)
            self.cancel.clicked.connect(self.reject)
            self.open_folder.clicked.connect(anki_util.open_user_files_folder)

        def _load_decks(self):
            self.decks.clear()
            decks = mw.col.decks.all()
            for deck in decks:
                name = deck.get("name")
                deck_id = deck.get("id")
                self.decks.addItem(name, deck_id)

        def _update_fields(self):
            self.fields.clear()
            self.expression_field.clear()
            self.reading_field.clear()

            deck_id = self.decks.currentData()
            if deck_id is None:
                return

            model_ids = mw.col.db.list("SELECT DISTINCT n.mid FROM notes n JOIN cards c ON n.id = c.nid WHERE c.did = ?", deck_id)

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
            logger.log.info(f"started tools backfill on {self.decks.currentText()}")
            if self.tab_widget.currentIndex() == 0:
                self._run_single_field()
            else:
                self._run_preset()
        
        def _run_single_field(self):
            deck_id = self.decks.currentData()
            expression_field = self.expression_field.currentText()
            reading_field = self.reading_field.currentText()
            field = self.fields.currentText()
            handlebars = [p.lstrip("{").rstrip("}") for p in self.yomitan_handlebars.text().split(",") if p.strip()]
            should_replace = self.replace.isChecked()
            
            note_ids = mw.col.db.list("SELECT DISTINCT nid FROM cards WHERE did = ?", deck_id)
            op = CollectionOp(
                parent = mw,
                op = lambda col: anki_util.backfill_notes(col, note_ids, expression_field, reading_field, [(field, handlebars, should_replace)])
            )
            
            op.success(anki_util.on_success).run_in_background()

        def _run_preset(self):
            deck_id = self.decks.currentData()
            expression_field = self.expression_field.currentText()
            reading_field = self.reading_field.currentText()
            target_tuples = []
            try:
                path = os.path.join(anki_util.get_user_files_dir(), self.preset.currentText())
                with open(path) as f:
                    preset = json.load(f)
                    targets = preset.get("targets")
                    for field, settings in targets.items():
                        handlebar = [p.lstrip("{").rstrip("}") for p in settings.get("handlebar").split(",") if p.strip()]
                        if not handlebar:
                            logger.log.error(f"handlebar for '{field}' empty in '{self.preset.currentText()}'")
                            showWarning(f"Handlebar for '{field}' should not be empty.<br>Please edit your preset file.")
                            return

                        should_replace = settings.get("replace")
                        if not isinstance(should_replace, bool):
                            logger.log.error(f"'replace' for '{field}' not boolean in '{self.preset.currentText()}'")
                            showWarning(f"'replace' for '{field}' must be boolean ('true' or 'false', without quotes).<br>Please edit your preset file.")
                            return

                        target_tuples.append((field, handlebar, should_replace))
            except json.JSONDecodeError as e:
                logger.log.error(e.msg)
                showWarning(f"Preset '{self.preset.currentText()}' contains errors.<br>Check the log for more information.")
                return
            except AttributeError as e:
                logger.log.error(e)
                showWarning(f"Preset '{self.preset.currentText()}' is missing key (targets, handlebar or replace).<br>Check the log for more information.")
                return
            except Exception as e:
                logger.log.error(e)
                showWarning(e)
                return

            note_ids = mw.col.db.list("SELECT DISTINCT nid FROM cards WHERE did = ?", deck_id)
            op = CollectionOp(
                parent = mw,
                op = lambda col: anki_util.backfill_notes(col, note_ids, expression_field, reading_field, target_tuples)
            )
            
            op.success(anki_util.on_success).run_in_background()