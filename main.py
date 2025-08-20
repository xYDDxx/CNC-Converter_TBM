import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QListView,
    QComboBox, QLineEdit, QCheckBox, QGridLayout, QHBoxLayout, QVBoxLayout,
    QFileDialog, QTreeView, QMessageBox
)
from PyQt6.QtGui import QPixmap, QFileSystemModel
from PyQt6.QtCore import Qt, QDir

# Backend
from logic.config_handler import load_config, update_config
from logic.excel_rules import load_rules_from_excel
from logic.converter import convert_single_file, batch_convert


class CNCConverterUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CNC-Konverter")
        self.setGeometry(200, 200, 1400, 800)

        # Config laden (fehlende Keys tolerant nachrüsten)
        self.config = load_config()
        self.config.setdefault("source_dir", "./input")
        self.config.setdefault("target_dir", "./output")
        self.config.setdefault("converter_dir", "./data")
        self.config.setdefault("excel_path", "")
        self.config.setdefault("active_source_file", "")

        # Haupt-Widget
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # Titel + Logo
        header_layout = QVBoxLayout()
        title_label = QLabel("<h2><i>CNC-Konverter</i></h2>")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_label = QLabel()
        logo_path = os.path.join("img", "tbm_peening_controls_kurz_7cm.png")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                200, 42,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(scaled_pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        logo_row = QHBoxLayout()
        logo_row.addStretch()
        logo_row.addWidget(logo_label)

        header_layout.addWidget(title_label)
        header_layout.addLayout(logo_row)
        main_layout.addLayout(header_layout)

        # Grid für Module mit größeren Abständen zwischen den Modulen
        grid = QGridLayout()
        grid.setHorizontalSpacing(40)
        grid.setVerticalSpacing(10)

        # Quell-Bereich
        self.add_source_section(grid, 0)

        # Konverter-Bereich
        self.add_converter_section(grid, 2)

        # Ziel-Bereich
        self.add_target_section(grid, 4)

        main_layout.addLayout(grid)

        # Untere Buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Konvertierung")
        self.abort_btn = QPushButton("Abbruch")
        self.exit_btn = QPushButton("Beenden")
        self.exit_btn.clicked.connect(self.close)
        self.start_btn.clicked.connect(self.start_conversion)

        btn_layout.addStretch()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.abort_btn)
        btn_layout.addWidget(self.exit_btn)
        main_layout.addLayout(btn_layout)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Nach Aufbau: Initiale Pfade in Views setzen
        self._apply_initial_paths_to_views()

    # ----------------- Abschnitte -----------------
    def add_source_section(self, grid, col_start):
        grid.addWidget(QLabel("Quellverzeichnis"), 0, col_start, 1, 2)

        self.src_dir_field = QLineEdit(self.config.get("source_dir", ""))
        self.src_dir_field.setPlaceholderText("Pfad zum Quellverzeichnis...")
        self.src_dir_btn = QPushButton("Durchsuchen")
        self.src_dir_btn.clicked.connect(
            lambda: self.select_directory(
                self.src_dir_field, self.src_tree, self.src_list, section="source"
            )
        )
        grid.addWidget(self.src_dir_field, 1, col_start)
        grid.addWidget(self.src_dir_btn, 1, col_start + 1)

        self.src_tree, self.src_list = self.create_explorer(section="source")
        pair_layout = QHBoxLayout()
        pair_layout.setSpacing(5)
        self.src_tree.setFixedHeight(400)
        self.src_list.setFixedHeight(400)
        pair_layout.addWidget(self.src_tree)
        pair_layout.addWidget(self.src_list)
        grid.addLayout(pair_layout, 2, col_start, 1, 2)

        self.chk_convert_all = QCheckBox("Konvertiere Alle")
        grid.addWidget(self.chk_convert_all, 3, col_start)

        # Feld für aktives Quellfile (statt Button)
        grid.addWidget(QLabel("Akt. Aktives Quellfile"), 4, col_start, 1, 2)
        self.active_src_file = QLineEdit()
        self.active_src_file.setPlaceholderText("Kein Quellfile ausgewählt")
        self.active_src_file.setReadOnly(True)
        # Falls in config vorhanden, Name anzeigen
        if self.config.get("active_source_file"):
            self.active_src_file.setText(os.path.basename(self.config["active_source_file"]))
        grid.addWidget(self.active_src_file, 5, col_start, 1, 2)

        # Präfix-UI (optisch wie gehabt; Logik-Hooks kommen später)
        grid.addWidget(QLabel("Quell-Dateinamen-Präfix abschneiden"), 6, col_start, 1, 2)
        grid.addWidget(QLabel("Anzahl Zeichen"), 7, col_start)
        self.src_prefix_count = QComboBox()
        self.src_prefix_count.addItems([str(i) for i in range(0, 11)])
        grid.addWidget(self.src_prefix_count, 7, col_start + 1)
        self.chk_src_spec = QCheckBox("Nur-Spezif-String")
        grid.addWidget(self.chk_src_spec, 8, col_start)
        self.src_prefix_str = QLineEdit()
        self.src_prefix_str.setPlaceholderText("Präfix-String-Q")
        grid.addWidget(self.src_prefix_str, 8, col_start + 1)

    def add_converter_section(self, grid, col_start):
        grid.addWidget(QLabel("Konverter-Verzeichnis"), 0, col_start, 1, 2)

        self.conv_dir_field = QLineEdit(self.config.get("converter_dir", ""))
        self.conv_dir_field.setPlaceholderText("Pfad zum Konverter-Verzeichnis...")
        self.conv_dir_btn = QPushButton("Durchsuchen")
        self.conv_dir_btn.clicked.connect(
            lambda: self.select_directory(
                self.conv_dir_field, self.conv_tree, self.conv_list, section="converter"
            )
        )
        grid.addWidget(self.conv_dir_field, 1, col_start)
        grid.addWidget(self.conv_dir_btn, 1, col_start + 1)

        self.conv_tree, self.conv_list = self.create_explorer(section="converter")
        pair_layout = QHBoxLayout()
        pair_layout.setSpacing(5)
        self.conv_tree.setFixedHeight(400)
        self.conv_list.setFixedHeight(400)
        pair_layout.addWidget(self.conv_tree)
        pair_layout.addWidget(self.conv_list)
        grid.addLayout(pair_layout, 2, col_start, 1, 2)

        # Aktives Konverter-File (Excel)
        grid.addWidget(QLabel("Aktives Konverter-File"), 3, col_start, 1, 2)
        self.active_conv_file = QLineEdit()
        self.active_conv_file.setPlaceholderText("Kein Konverter-File ausgewählt")
        self.active_conv_file.setReadOnly(True)
        if self.config.get("excel_path"):
            self.active_conv_file.setText(os.path.basename(self.config["excel_path"]))
        grid.addWidget(self.active_conv_file, 4, col_start, 1, 2)

        # Datei-Endungen Q -> Z (optisch wie gehabt; Logik später)
        grid.addWidget(QLabel("Datei Endungen Q -> Z"), 5, col_start, 1, 2)
        self.endings_q = [QLineEdit() for _ in range(3)]
        self.endings_z = [QLineEdit() for _ in range(3)]
        for i in range(3):
            self.endings_q[i].setPlaceholderText(f"Q-End{i+1}")
            self.endings_z[i].setPlaceholderText(f"Z-End{i+1}")
            grid.addWidget(self.endings_q[i], 6 + i, col_start)
            grid.addWidget(self.endings_z[i], 6 + i, col_start + 1)

    def add_target_section(self, grid, col_start):
        grid.addWidget(QLabel("Zielverzeichnis"), 0, col_start, 1, 2)

        self.dst_dir_field = QLineEdit(self.config.get("target_dir", ""))
        self.dst_dir_field.setPlaceholderText("Pfad zum Zielverzeichnis...")
        self.dst_dir_btn = QPushButton("Durchsuchen")
        self.dst_dir_btn.clicked.connect(
            lambda: self.select_directory(
                self.dst_dir_field, self.dst_tree, self.dst_list, section="target"
            )
        )
        grid.addWidget(self.dst_dir_field, 1, col_start)
        grid.addWidget(self.dst_dir_btn, 1, col_start + 1)

        self.dst_tree, self.dst_list = self.create_explorer(section="target")
        pair_layout = QHBoxLayout()
        pair_layout.setSpacing(5)
        self.dst_tree.setFixedHeight(400)
        self.dst_list.setFixedHeight(400)
        pair_layout.addWidget(self.dst_tree)
        pair_layout.addWidget(self.dst_list)
        grid.addLayout(pair_layout, 2, col_start, 1, 2)

        # Ziel-Präfix-Einstellungen (optisch beibehalten)
        grid.addWidget(QLabel("Ziel-Dateinamen-Präfix anhängen"), 4, col_start, 1, 2)
        grid.addWidget(QLabel("Anzahl Zeichen"), 5, col_start)
        self.dst_prefix_count = QComboBox()
        self.dst_prefix_count.addItems([str(i) for i in range(0, 11)])
        grid.addWidget(self.dst_prefix_count, 5, col_start + 1)
        self.chk_dst_spec = QCheckBox("Nur-Spezif-String")
        grid.addWidget(self.chk_dst_spec, 6, col_start)
        self.dst_prefix_str = QLineEdit()
        self.dst_prefix_str.setPlaceholderText("Präfix-String-Z")
        grid.addWidget(self.dst_prefix_str, 6, col_start + 1)

    # ----------------- Explorer-View -----------------
    def create_explorer(self, section: str):
        model = QFileSystemModel()
        model.setRootPath(QDir.rootPath())

        tree = QTreeView()
        tree.setModel(model)
        tree.setRootIndex(model.index(QDir.rootPath()))
        tree.setColumnWidth(0, 150)
        tree.setHeaderHidden(True)

        list_view = QListView()
        list_view.setModel(model)

        # Klick auf Tree: Ordner in der Liste anzeigen
        def on_tree_clicked(index):
            path = model.filePath(index)
            if os.path.isdir(path):
                list_view.setRootIndex(model.index(path))

        tree.clicked.connect(on_tree_clicked)

        # Doppelklick auf Datei in Liste: aktive Datei setzen
        def on_list_double_clicked(index):
            path = model.filePath(index)
            if not os.path.isfile(path):
                return

            if section == "source":
                # aktives Quellfile setzen (Name anzeigen, Pfad speichern)
                self.active_src_file.setText(os.path.basename(path))
                update_config("active_source_file", path)
            elif section == "converter":
                # Nur Excel erlauben
                if path.lower().endswith((".xlsx", ".xls")):
                    self.active_conv_file.setText(os.path.basename(path))
                    update_config("excel_path", path)
                else:
                    QMessageBox.information(
                        self, "Hinweis",
                        "Bitte ein Excel-File (*.xlsx / *.xls) per Doppelklick wählen."
                    )
            else:
                # target: keine Datei-Auswahl nötig
                pass

        list_view.doubleClicked.connect(on_list_double_clicked)
        return tree, list_view

    # ----------------- Backend Hooks -----------------
    def _apply_initial_paths_to_views(self):
        # Source
        if self.src_dir_field.text().strip():
            model = self.src_tree.model()
            p = self.src_dir_field.text().strip()
            self.src_tree.setRootIndex(model.index(p))
            self.src_list.setRootIndex(model.index(p))
        # Converter
        if self.conv_dir_field.text().strip():
            model = self.conv_tree.model()
            p = self.conv_dir_field.text().strip()
            self.conv_tree.setRootIndex(model.index(p))
            self.conv_list.setRootIndex(model.index(p))
        # Target
        if self.dst_dir_field.text().strip():
            model = self.dst_tree.model()
            p = self.dst_dir_field.text().strip()
            self.dst_tree.setRootIndex(model.index(p))
            self.dst_list.setRootIndex(model.index(p))

    def select_directory(self, path_field, tree_view, list_view, section: str):
        directory = QFileDialog.getExistingDirectory(
            self, "Verzeichnis auswählen",
            path_field.text().strip() or QDir.homePath()
        )
        if directory:
            path_field.setText(directory)
            model = tree_view.model()
            tree_view.setRootIndex(model.index(directory))
            list_view.setRootIndex(model.index(directory))

            # Persistieren
            if section == "source":
                update_config("source_dir", directory)
            elif section == "converter":
                update_config("converter_dir", directory)
            elif section == "target":
                update_config("target_dir", directory)

    def start_conversion(self):
        try:
            source_dir = self.src_dir_field.text().strip()
            target_dir = self.dst_dir_field.text().strip()
            excel_path = self._resolve_excel_path()

            if not os.path.isdir(source_dir):
                QMessageBox.critical(self, "Fehler", "Bitte ein gültiges Quellverzeichnis wählen.")
                return
            if not os.path.isdir(target_dir):
                QMessageBox.critical(self, "Fehler", "Bitte ein gültiges Zielverzeichnis wählen.")
                return
            if not (excel_path and os.path.isfile(excel_path)):
                QMessageBox.critical(self, "Fehler", "Bitte ein gültiges Konverter-Excel per Doppelklick wählen.")
                return

            rules = load_rules_from_excel(excel_path)

            if self.chk_convert_all.isChecked():
                # Batch
                batch_convert(
                    source_dir, target_dir, rules,
                    cut_prefix="", add_prefix="_Z", new_ext=".ZNC"
                )
                QMessageBox.information(self, "Batch", "Alle Dateien erfolgreich konvertiert.")
            else:
                # Einzeldatei über aktives Quellfile
                active_src_path = self._resolve_active_source_file()
                if not active_src_path:
                    QMessageBox.information(
                        self, "Hinweis",
                        "Bitte im Quell-ListView per Doppelklick eine Datei wählen (Akt. Aktives Quellfile)."
                    )
                    return
                convert_single_file(
                    active_src_path, target_dir, rules,
                    cut_prefix="", add_prefix="_Z", new_ext=".ZNC"
                )
                QMessageBox.information(
                    self, "Erfolg",
                    f"Datei erfolgreich konvertiert:\n{os.path.basename(active_src_path)}"
                )

            # Nachlauf: Ziel-Ansicht aktualisieren
            self._refresh_target_view()

        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler bei der Konvertierung:\n{str(e)}")

    def _resolve_excel_path(self) -> str:
        # bevorzugt config, da dort der volle Pfad liegt
        excel = load_config().get("excel_path", "")  # frisch lesen
        if excel and os.path.isfile(excel):
            return excel
        # Fallback: nichts
        return ""

    def _resolve_active_source_file(self) -> str:
        cfg = load_config()
        active = cfg.get("active_source_file", "")
        if active and os.path.isfile(active):
            return active
        return ""

    def _refresh_target_view(self):
        model = self.dst_tree.model()
        path = self.dst_dir_field.text().strip()
        if path and os.path.isdir(path):
            self.dst_tree.setRootIndex(model.index(path))
            self.dst_list.setRootIndex(model.index(path))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CNCConverterUI()
    window.show()
    sys.exit(app.exec())
