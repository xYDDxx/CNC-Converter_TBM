import sys
import os
import subprocess
import platform
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QListView,
    QComboBox, QLineEdit, QCheckBox, QGridLayout, QHBoxLayout, QVBoxLayout,
    QFileDialog, QTreeView, QMessageBox, QDialog
)
from PyQt6.QtGui import QPixmap, QFileSystemModel
from PyQt6.QtCore import Qt, QDir

# Backend
from logic.config_handler import load_config, update_config, save_config
from logic.excel_rules import load_rules_from_excel
from logic.converter import convert_single_file, batch_convert
from logic.file_handler import validate_filename_settings
from logic.logger import setup_logger, get_logger, log_config_change
from logic.validation import comprehensive_validation
from progress_dialog import ProgressDialog


class CNCConverterUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CNC-Konverter")
        self.setGeometry(200, 200, 1400, 800)

        # Logging initialisieren
        setup_logger()
        self.logger = get_logger()
        self.logger.info("=== CNC-Konverter gestartet ===")

        # Config laden
        self.config = load_config()
        
        # Aktueller Pfad für ListViews speichern
        self.current_source_listview_path = ""
        self.current_target_listview_path = ""
        self.current_converter_listview_path = ""
        self.last_converted_file = ""
        
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

        # Grid für Module
        grid = QGridLayout()
        grid.setHorizontalSpacing(40)
        grid.setVerticalSpacing(10)

        # Abschnitte
        self.add_source_section(grid, 0)
        self.add_converter_section(grid, 2)
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

        # Nach Aufbau: Initiale Pfade setzen und Config laden
        self._apply_initial_paths_to_views()
        self._load_config_to_ui()

    # ----------------- Abschnitte -----------------
    def add_source_section(self, grid, col_start):
        grid.addWidget(QLabel("Quellverzeichnis"), 0, col_start, 1, 2)

        # Layout für Pfad-Feld und Button
        path_layout = QHBoxLayout()
        
        self.src_dir_field = QPushButton()  # Button statt LineEdit
        self.src_dir_field.setText(self.config.get("source_dir", "Pfad zum Quellverzeichnis auswählen..."))
       
        self.src_dir_field.clicked.connect(lambda: self.select_directory_via_field("source"))
        
        self.src_open_btn = QPushButton("Q-File-öffnen")
        self.src_open_btn.clicked.connect(lambda: self.open_file_in_editor("source"))
        self.src_open_btn.setFixedWidth(self.src_open_btn.sizeHint().width())
        
        path_layout.addWidget(self.src_dir_field)
        path_layout.addWidget(self.src_open_btn)
        
        grid.addLayout(path_layout, 1, col_start, 1, 2)

        self.src_tree, self.src_list = self.create_explorer(section="source")
        pair_layout = QHBoxLayout()
        pair_layout.setSpacing(5)
        self.src_tree.setFixedHeight(400)
        self.src_list.setFixedHeight(400)
        pair_layout.addWidget(self.src_tree)
        pair_layout.addWidget(self.src_list)
        grid.addLayout(pair_layout, 2, col_start, 1, 2)

        self.chk_convert_all = QCheckBox("Konvertiere Alle")
        self.chk_convert_all.stateChanged.connect(self._toggle_batch_mode)
        grid.addWidget(self.chk_convert_all, 3, col_start)

        # Feld für aktives Quellfile
        grid.addWidget(QLabel("Akt. Aktives Quellfile"), 4, col_start, 1, 2)
        self.active_src_file = QLineEdit()
        self.active_src_file.setPlaceholderText("Kein Quellfile ausgewählt")
        self.active_src_file.setReadOnly(True)
        grid.addWidget(self.active_src_file, 5, col_start, 1, 2)

        # Präfix-UI - Quelle
        grid.addWidget(QLabel("Quell-Dateinamen-Präfix abschneiden"), 6, col_start, 1, 2)
        grid.addWidget(QLabel("Anzahl Zeichen"), 7, col_start)
        self.src_prefix_count = QComboBox()
        self.src_prefix_count.addItems([str(i) for i in range(0, 11)])
        self.src_prefix_count.currentTextChanged.connect(self._save_prefix_settings)
        grid.addWidget(self.src_prefix_count, 7, col_start + 1)
        
        self.chk_src_spec = QCheckBox("Nur-Spezif-String")
        self.chk_src_spec.stateChanged.connect(self._save_prefix_settings)
        grid.addWidget(self.chk_src_spec, 8, col_start)
        
        self.src_prefix_str = QLineEdit()
        self.src_prefix_str.setPlaceholderText("Präfix-String-Q")
        self.src_prefix_str.textChanged.connect(self._save_prefix_settings)
        grid.addWidget(self.src_prefix_str, 8, col_start + 1)

    def add_converter_section(self, grid, col_start):
        grid.addWidget(QLabel("Konverter-Verzeichnis"), 0, col_start, 1, 2)

        # Layout für Pfad-Feld und Button
        path_layout = QHBoxLayout()
        
        self.conv_dir_field = QPushButton()  # Button statt LineEdit
        self.conv_dir_field.setText(self.config.get("converter_dir", "Pfad zum Konverter-Verzeichnis auswählen..."))
        
        self.conv_dir_field.clicked.connect(lambda: self.select_directory_via_field("converter"))
        
        self.conv_open_btn = QPushButton("Excel-öffnen")
        self.conv_open_btn.clicked.connect(lambda: self.open_file_in_editor("converter"))
        self.conv_open_btn.setFixedWidth(self.conv_open_btn.sizeHint().width())
        
        path_layout.addWidget(self.conv_dir_field)
        path_layout.addWidget(self.conv_open_btn)
        
        grid.addLayout(path_layout, 1, col_start, 1, 2)

        self.conv_tree, self.conv_list = self.create_explorer(section="converter")
        pair_layout = QHBoxLayout()
        pair_layout.setSpacing(5)
        self.conv_tree.setFixedHeight(400)
        self.conv_list.setFixedHeight(400)
        pair_layout.addWidget(self.conv_tree)
        pair_layout.addWidget(self.conv_list)
        grid.addLayout(pair_layout, 2, col_start, 1, 2)

        # Aktives Konverter-File
        grid.addWidget(QLabel("Aktives Konverter-File"), 3, col_start, 1, 2)
        self.active_conv_file = QLineEdit()
        self.active_conv_file.setPlaceholderText("Kein Konverter-File ausgewählt")
        self.active_conv_file.setReadOnly(True)
        grid.addWidget(self.active_conv_file, 4, col_start, 1, 2)

        # Datei-Endungen Q -> Z
        grid.addWidget(QLabel("Datei Endungen Q -> Z"), 5, col_start, 1, 2)
        self.endings_q = [QLineEdit() for _ in range(3)]
        self.endings_z = [QLineEdit() for _ in range(3)]
        for i in range(3):
            self.endings_q[i].setPlaceholderText(f"Q-End{i+1}")
            self.endings_z[i].setPlaceholderText(f"Z-End{i+1}")
            self.endings_q[i].textChanged.connect(self._save_ending_settings)
            self.endings_z[i].textChanged.connect(self._save_ending_settings)
            grid.addWidget(self.endings_q[i], 6 + i, col_start)
            grid.addWidget(self.endings_z[i], 6 + i, col_start + 1)

    def add_target_section(self, grid, col_start):
        grid.addWidget(QLabel("Zielverzeichnis"), 0, col_start, 1, 2)

        # Layout für Pfad-Feld und Button
        path_layout = QHBoxLayout()
        
        self.dst_dir_field = QPushButton()  # Button statt LineEdit
        self.dst_dir_field.setText(self.config.get("target_dir", "Pfad zum Zielverzeichnis auswählen..."))
        
        self.dst_dir_field.clicked.connect(lambda: self.select_directory_via_field("target"))
        
        self.dst_open_btn = QPushButton("Z-File-öffnen")
        self.dst_open_btn.clicked.connect(lambda: self.open_file_in_editor("target"))
        self.dst_open_btn.setFixedWidth(self.dst_open_btn.sizeHint().width())
        
        path_layout.addWidget(self.dst_dir_field)
        path_layout.addWidget(self.dst_open_btn)
        
        grid.addLayout(path_layout, 1, col_start, 1, 2)

        self.dst_tree, self.dst_list = self.create_explorer(section="target")
        pair_layout = QHBoxLayout()
        pair_layout.setSpacing(5)
        self.dst_tree.setFixedHeight(400)
        self.dst_list.setFixedHeight(400)
        pair_layout.addWidget(self.dst_tree)
        pair_layout.addWidget(self.dst_list)
        grid.addLayout(pair_layout, 2, col_start, 1, 2)

        # Ziel-Präfix
        grid.addWidget(QLabel("Ziel-Dateinamen-Präfix anhängen"), 4, col_start, 1, 2)
        grid.addWidget(QLabel("Anzahl Zeichen"), 5, col_start)
        self.dst_prefix_count = QComboBox()
        self.dst_prefix_count.addItems([str(i) for i in range(0, 11)])
        self.dst_prefix_count.currentTextChanged.connect(self._save_prefix_settings)
        grid.addWidget(self.dst_prefix_count, 5, col_start + 1)
        
        self.chk_dst_spec = QCheckBox("Nur-Spezif-String")
        self.chk_dst_spec.stateChanged.connect(self._save_prefix_settings)
        grid.addWidget(self.chk_dst_spec, 6, col_start)
        
        self.dst_prefix_str = QLineEdit()
        self.dst_prefix_str.setPlaceholderText("Präfix-String-Z")
        self.dst_prefix_str.textChanged.connect(self._save_prefix_settings)
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

        def on_tree_clicked(index):
            path = model.filePath(index)
            if os.path.isdir(path):
                list_view.setRootIndex(model.index(path))
                # Aktuellen ListView-Pfad speichern
                if section == "source":
                    self.current_source_listview_path = path
                elif section == "converter":
                    self.current_converter_listview_path = path
                elif section == "target":
                    self.current_target_listview_path = path

        tree.clicked.connect(on_tree_clicked)

        def on_list_double_clicked(index):
            path = model.filePath(index)
            if not os.path.isfile(path):
                return

            if section == "source":
                self.active_src_file.setText(os.path.basename(path))
                update_config("active_source_file", path)
            elif section == "converter":
                if path.lower().endswith((".xlsx", ".xls")):
                    self.active_conv_file.setText(os.path.basename(path))
                    update_config("excel_path", path)
                else:
                    QMessageBox.information(
                        self, "Hinweis",
                        "Bitte ein Excel-File (*.xlsx / *.xls) wählen."
                    )

        list_view.doubleClicked.connect(on_list_double_clicked)
        return tree, list_view

    # ----------------- Neue Methoden für Pfad-Auswahl und Datei-Öffnung -----------------
    def select_directory_via_field(self, section: str):
        """Öffnet den Dateidialog zur Pfad-Auswahl mit Validierung."""
        current_path = ""
        if section == "source":
            current_path = self.config.get("source_dir", "")
        elif section == "converter":
            current_path = self.config.get("converter_dir", "")
        elif section == "target":
            current_path = self.config.get("target_dir", "")
        
        directory = QFileDialog.getExistingDirectory(
            self, "Verzeichnis auswählen",
            current_path or QDir.homePath()
        )
        
        if directory:
            # Zusätzliche Validierung für Zielverzeichnis
            if section == "target":
                source_dir = self.config.get("source_dir", "")
                if source_dir and os.path.samefile(directory, source_dir):
                    QMessageBox.warning(
                        self, "Ungültiges Verzeichnis", 
                        "Ziel- und Quellverzeichnis dürfen nicht identisch sein."
                    )
                    return
            
            # Button-Text und Config aktualisieren
            if section == "source":
                self.src_dir_field.setText(directory)
                log_config_change("source_dir", self.config.get("source_dir"), directory)
                update_config("source_dir", directory)
                model = self.src_tree.model()
                self.src_tree.setRootIndex(model.index(directory))
                self.src_list.setRootIndex(model.index(directory))
                self.current_source_listview_path = directory
            elif section == "converter":
                self.conv_dir_field.setText(directory)
                update_config("converter_dir", directory)
                model = self.conv_tree.model()
                self.conv_tree.setRootIndex(model.index(directory))
                self.conv_list.setRootIndex(model.index(directory))
                self.current_converter_listview_path = directory
            elif section == "target":
                self.dst_dir_field.setText(directory)
                update_config("target_dir", directory)
                model = self.dst_tree.model()
                self.dst_tree.setRootIndex(model.index(directory))
                self.dst_list.setRootIndex(model.index(directory))
                self.current_target_listview_path = directory

        self.logger.info(f"Verzeichnis ausgewählt ({section}): {directory}")

    def open_file_in_editor(self, section: str):
        """Öffnet die entsprechende Datei im passenden Editor."""
        file_path = ""
        
        if section == "source":
            # Ausgewählte Quelldatei öffnen
            active_src = self.config.get("active_source_file", "")
            if active_src and os.path.isfile(active_src):
                file_path = active_src
            else:
                QMessageBox.information(self, "Hinweis", "Keine Quelldatei ausgewählt.")
                return
            self._open_in_text_editor(file_path)
                
        elif section == "converter":
            # Excel-Datei öffnen
            excel_path = self.config.get("excel_path", "")
            if excel_path and os.path.isfile(excel_path):
                file_path = excel_path
            else:
                QMessageBox.information(self, "Hinweis", "Keine Excel-Datei ausgewählt.")
                return
            self._open_in_excel(file_path)
                
        elif section == "target":
            # Zuerst prüfen ob im ListView eine Datei ausgewählt ist
            selected_indexes = self.dst_list.selectedIndexes()
            if selected_indexes:
                model = self.dst_list.model()
                selected_path = model.filePath(selected_indexes[0])
                if os.path.isfile(selected_path):
                    file_path = selected_path
            
            # Falls keine ListView-Auswahl, dann letztes konvertiertes File
            if not file_path and self.last_converted_file and os.path.isfile(self.last_converted_file):
                file_path = self.last_converted_file
            
            if file_path:
                self._open_in_text_editor(file_path)
            else:
                QMessageBox.information(self, "Hinweis", "Keine Zieldatei verfügbar.")

    def _open_in_text_editor(self, file_path: str):
        """Öffnet Datei in Notepad++ oder anderem Texteditor."""
        try:
            system = platform.system()
            if system == "Windows":
                # Erst Notepad++ versuchen
                notepad_paths = [
                    r"C:\Program Files\Notepad++\notepad++.exe",
                    r"C:\Program Files (x86)\Notepad++\notepad++.exe"
                ]
                
                for npp_path in notepad_paths:
                    if os.path.exists(npp_path):
                        subprocess.run([npp_path, file_path], check=False)
                        return
                
                # Fallback: Windows Notepad
                subprocess.run(["notepad.exe", file_path], check=False)
            else:
                # Linux/Mac: Standard-Texteditor verwenden
                if system == "Darwin":  # macOS
                    subprocess.run(["open", "-t", file_path], check=False)
                else:  # Linux
                    subprocess.run(["xdg-open", file_path], check=False)
                    
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Datei konnte nicht geöffnet werden:\n{str(e)}")

    def _open_in_excel(self, file_path: str):
        """Öffnet Excel-Datei in Excel oder LibreOffice."""
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(file_path)  # Windows: Standard-Programm verwenden
            elif system == "Darwin":  # macOS
                subprocess.run(["open", file_path], check=False)
            else:  # Linux
                subprocess.run(["xdg-open", file_path], check=False)
                
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Excel-Datei konnte nicht geöffnet werden:\n{str(e)}")

    # ----------------- Config Management -----------------
    def _load_config_to_ui(self):
        """Lädt die gespeicherte Konfiguration in die UI-Elemente."""
        # Button-Texte setzen
        self.src_dir_field.setText(self.config.get("source_dir", "Pfad zum Quellverzeichnis auswählen..."))
        self.conv_dir_field.setText(self.config.get("converter_dir", "Pfad zum Konverter-Verzeichnis auswählen..."))
        self.dst_dir_field.setText(self.config.get("target_dir", "Pfad zum Zielverzeichnis auswählen..."))
        
        # Aktive Dateien anzeigen
        if self.config.get("active_source_file"):
            self.active_src_file.setText(os.path.basename(self.config["active_source_file"]))
        if self.config.get("excel_path"):
            self.active_conv_file.setText(os.path.basename(self.config["excel_path"]))

        # Präfix-Einstellungen laden
        self.src_prefix_count.setCurrentText(str(self.config.get("source_prefix_count", 0)))
        self.chk_src_spec.setChecked(self.config.get("source_prefix_specific", False))
        self.src_prefix_str.setText(self.config.get("source_prefix_string", ""))

        self.dst_prefix_count.setCurrentText(str(self.config.get("target_prefix_count", 0)))
        self.chk_dst_spec.setChecked(self.config.get("target_prefix_specific", False))
        self.dst_prefix_str.setText(self.config.get("target_prefix_string", "_Z"))

        # Dateiendungen laden
        file_endings = self.config.get("file_endings", [])
        for i in range(min(3, len(file_endings))):
            if i < len(file_endings):
                self.endings_q[i].setText(file_endings[i].get("source", ""))
                self.endings_z[i].setText(file_endings[i].get("target", ""))

    def _save_prefix_settings(self):
        """Speichert die aktuellen Präfix-Einstellungen in die Config mit Logging."""
        old_config = self.config.copy()
        
        config_updates = {
            "source_prefix_count": int(self.src_prefix_count.currentText()),
            "source_prefix_specific": self.chk_src_spec.isChecked(),
            "source_prefix_string": self.src_prefix_str.text(),
            "target_prefix_count": int(self.dst_prefix_count.currentText()),
            "target_prefix_specific": self.chk_dst_spec.isChecked(),
            "target_prefix_string": self.dst_prefix_str.text()
        }
        
        # Config aktualisieren mit Logging
        for key, value in config_updates.items():
            old_value = self.config.get(key)
            if old_value != value:
                log_config_change(key, old_value, value)
            self.config[key] = value
            
        save_config(self.config)

    def _save_ending_settings(self):
        """Speichert die aktuellen Präfix-Einstellungen in die Config mit Logging."""
        old_config = self.config.copy()
        
        config_updates = {
            "source_prefix_count": int(self.src_prefix_count.currentText()),
            "source_prefix_specific": self.chk_src_spec.isChecked(),
            "source_prefix_string": self.src_prefix_str.text(),
            "target_prefix_count": int(self.dst_prefix_count.currentText()),
            "target_prefix_specific": self.chk_dst_spec.isChecked(),
            "target_prefix_string": self.dst_prefix_str.text()
        }
        
        # Config aktualisieren mit Logging
        for key, value in config_updates.items():
            old_value = self.config.get(key)
            if old_value != value:
                log_config_change(key, old_value, value)
            self.config[key] = value
            
        save_config(self.config)

    # ----------------- Batch Umschalter -----------------
    def _toggle_batch_mode(self, state):
        if self.chk_convert_all.isChecked():
            self.active_src_file.setText("Batch Konvertierung aktiv")
            self.active_src_file.setEnabled(False)
        else:
            self.active_src_file.setEnabled(True)
            active = self.config.get("active_source_file", "")
            if active:
                self.active_src_file.setText(os.path.basename(active))
            else:
                self.active_src_file.clear()
                self.active_src_file.setPlaceholderText("Kein Quellfile ausgewählt")

    # ----------------- Backend Hooks -----------------
    def _apply_initial_paths_to_views(self):
        for config_key, tree, lst, attr in [
            ("source_dir", self.src_tree, self.src_list, "current_source_listview_path"),
            ("converter_dir", self.conv_tree, self.conv_list, "current_converter_listview_path"),
            ("target_dir", self.dst_tree, self.dst_list, "current_target_listview_path")
        ]:
            path = self.config.get(config_key, "")
            if path and os.path.exists(path):
                model = tree.model()
                tree.setRootIndex(model.index(path))
                lst.setRootIndex(model.index(path))
                setattr(self, attr, path)

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
            update_config(section + "_dir", directory)

    def _validate_settings(self) -> tuple[bool, list[str]]:
        """Validiert alle Einstellungen mit umfassendem Validation-Modul."""
        try:
            # Bei Batch-Modus: ListView-Pfad als source_dir verwenden
            config_copy = self.config.copy()
            if self.chk_convert_all.isChecked() and self.current_source_listview_path:
                config_copy["source_dir"] = self.current_source_listview_path
            
            batch_mode = self.chk_convert_all.isChecked()
            is_valid, errors = comprehensive_validation(config_copy, batch_mode)
            
            return is_valid, errors
            
        except Exception as e:
            self.logger.error(f"Validierungsfehler: {str(e)}")
            return False, [f"Unerwarteter Validierungsfehler: {str(e)}"]

    def start_conversion(self):
        """Startet die Konvertierung mit Progress-Dialog."""
        try:
            self.logger.info("Konvertierung angefordert vom Benutzer")
            
            # Einstellungen validieren
            is_valid, errors = self._validate_settings()
            if not is_valid:
                error_text = "\n• ".join(["Folgende Fehler müssen behoben werden:"] + errors)
                QMessageBox.critical(self, "Validierungsfehler", error_text)
                self.logger.warning(f"Validierung fehlgeschlagen: {len(errors)} Fehler")
                return

            # Parameter für Konvertierung sammeln
            conversion_params = self._gather_conversion_parameters()
            
            # Progress-Dialog erstellen und anzeigen
            title = "Batch-Konvertierung läuft..." if self.chk_convert_all.isChecked() else "Datei wird konvertiert..."
            progress_dialog = ProgressDialog(self, title)
            
            # Konvertierung im Progress-Dialog starten
            if self.chk_convert_all.isChecked():
                progress_dialog.start_conversion(self._run_batch_conversion, **conversion_params)
            else:
                progress_dialog.start_conversion(self._run_single_conversion, **conversion_params)
            
            # Dialog anzeigen (modal)
            result = progress_dialog.exec()
            
            # Nach Abschluss: Ziel-View aktualisieren
            if result == QDialog.DialogCode.Accepted:
                self._refresh_target_view()
                
        except Exception as e:
            error_msg = f"Unerwarteter Fehler beim Starten der Konvertierung: {str(e)}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "Fehler", error_msg)

    def _gather_conversion_parameters(self) -> dict:
        """Sammelt alle Parameter für die Konvertierung."""
        target_dir = self.config.get("target_dir", "")
        excel_path = self.config["excel_path"]
        
        # Bei Batch-Modus: ListView-Pfad als Quellverzeichnis verwenden
        if self.chk_convert_all.isChecked():
            source_dir = self.current_source_listview_path or self.config.get("source_dir", "")
        else:
            source_dir = self.config.get("source_dir", "")
        
        # Dateiendungen-Parameter
        file_endings = []
        for i in range(3):
            source_end = self.endings_q[i].text().strip()
            target_end = self.endings_z[i].text().strip()
            if source_end or target_end:
                file_endings.append({"source": source_end, "target": target_end})

        return {
            'source_dir': source_dir,
            'target_dir': target_dir,
            'excel_path': excel_path,
            'source_prefix_count': int(self.src_prefix_count.currentText()),
            'source_prefix_specific': self.chk_src_spec.isChecked(),
            'source_prefix_string': self.src_prefix_str.text(),
            'target_prefix_count': int(self.dst_prefix_count.currentText()),
            'target_prefix_specific': self.chk_dst_spec.isChecked(),
            'target_prefix_string': self.dst_prefix_str.text(),
            'file_endings': file_endings,
            'active_source_file': self.config.get("active_source_file", "")
        }

    def _run_batch_conversion(self, source_dir, target_dir, excel_path, 
                            source_prefix_count, source_prefix_specific, source_prefix_string,
                            target_prefix_count, target_prefix_specific, target_prefix_string,
                            file_endings, progress_callback=None, cancel_check=None, **kwargs):
        """Führt Batch-Konvertierung aus."""
        from logic.excel_rules import load_rules_from_excel
        from logic.converter import batch_convert
        
        # Excel-Regeln laden
        rules = load_rules_from_excel(excel_path)
        self.logger.info(f"Excel-Regeln geladen: {len(rules)} Einträge")
        
        # Batch-Konvertierung starten
        return batch_convert(
            source_dir, target_dir, rules,
            source_prefix_count=source_prefix_count,
            source_prefix_specific=source_prefix_specific,
            source_prefix_string=source_prefix_string,
            target_prefix_count=target_prefix_count,
            target_prefix_specific=target_prefix_specific,
            target_prefix_string=target_prefix_string,
            file_endings=file_endings,
            progress_callback=progress_callback,
            cancel_check=cancel_check
        )

    def _run_single_conversion(self, target_dir, excel_path, active_source_file,
                             source_prefix_count, source_prefix_specific, source_prefix_string,
                             target_prefix_count, target_prefix_specific, target_prefix_string,
                             file_endings, progress_callback=None, cancel_check=None, **kwargs):
        """Führt Einzeldatei-Konvertierung aus."""
        from logic.excel_rules import load_rules_from_excel
        from logic.converter import convert_single_file
        
        # Excel-Regeln laden
        rules = load_rules_from_excel(excel_path)
        self.logger.info(f"Excel-Regeln geladen: {len(rules)} Einträge")
        
        # Einzeldatei-Konvertierung
        result_path = convert_single_file(
            active_source_file, target_dir, rules,
            source_prefix_count=source_prefix_count,
            source_prefix_specific=source_prefix_specific,
            source_prefix_string=source_prefix_string,
            target_prefix_count=target_prefix_count,
            target_prefix_specific=target_prefix_specific,
            target_prefix_string=target_prefix_string,
            file_endings=file_endings,
            progress_callback=progress_callback,
            cancel_check=cancel_check
        )
        
        self.last_converted_file = result_path
        return {'success': 1, 'failed': 0, 'total': 1}


    def _refresh_target_view(self):
        """Aktualisiert die Ziel-Verzeichnis-Ansicht."""
        model = self.dst_tree.model()
        path = self.config.get("target_dir", "")
        if path and os.path.isdir(path):
            # Model refresh erzwingen
            model.setRootPath(path)
            self.dst_tree.setRootIndex(model.index(path))
            self.dst_list.setRootIndex(model.index(path))
    
    def closeEvent(self, event):
        """Behandelt das Schließen der Anwendung."""
        self.logger.info("=== CNC-Konverter beendet ===")
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CNCConverterUI()
    window.show()
    sys.exit(app.exec())