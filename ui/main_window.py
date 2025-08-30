import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QGridLayout, QHBoxLayout, QVBoxLayout,
    QMessageBox, QDialog
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

# Backend-Module importieren
from logic.config_handler import load_config, save_config
from logic.excel_rules import load_rules_from_excel
from logic.converter import convert_single_file, batch_convert
from logic.logger import setup_logger, get_logger
from logic.validation import comprehensive_validation
from progress_dialog import ProgressDialog

# UI-Komponenten importieren
from .components.file_explorer_factory import FileExplorerFactory
from .components.directory_selector import DirectorySelector
from .components.file_opener import FileOpener
from .components.config_manager import ConfigManager
from .sections.source_section import SourceSection
from .sections.converter_section import ConverterSection
from .sections.target_section import TargetSection


class CNCConverterUI(QMainWindow):
    """Hauptfenster des CNC-Konverters mit vollständiger Benutzeroberfläche."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CNC-Konverter")
        # Fenster maximiert setzen
        self.setWindowState(Qt.WindowState.WindowMaximized)

        # Logging-System initialisieren
        setup_logger()
        self.logger = get_logger()
        self.logger.info("=== CNC-Konverter gestartet ===")

        # Flag für Config-Laden initialisieren
        self._loading_config = False
        
        # Konfiguration laden
        self.config = load_config()
        self.logger.info("Konfiguration erfolgreich geladen")
        
        # Aktuelle Pfade für ListViews speichern
        self.current_source_listview_path = ""
        self.current_target_listview_path = ""
        self.current_converter_listview_path = ""
        self.last_converted_file = ""
        
        # UI-Komponenten initialisieren
        self._init_components()
        
        # Benutzeroberfläche aufbauen
        self._setup_ui()
        
        # Initiale Konfiguration einmalig anwenden
        self.config_manager.apply_initial_paths_to_views()
        self.config_manager.load_config_to_ui()

    def _init_components(self):
        """Initialisiert alle UI-Komponenten."""
        # Factory für File-Explorer
        self.file_explorer_factory = FileExplorerFactory(self)
        
        # Komponenten
        self.directory_selector = DirectorySelector(self)
        self.file_opener = FileOpener(self)
        self.config_manager = ConfigManager(self)
        
        # Sections
        self.source_section = SourceSection(self)
        self.converter_section = ConverterSection(self)
        self.target_section = TargetSection(self)

    def _setup_ui(self):
        """Erstellt die komplette Benutzeroberfläche."""
        # Haupt-Widget und Layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # Header mit Titel und Logo
        self._setup_header(main_layout)

        # Grid-Layout für die drei Hauptbereiche (Quelle, Konverter, Ziel)
        self._setup_main_grid(main_layout)
        
        # Untere Button-Leiste (Reset, Start, Abbruch, Beenden)
        self._setup_button_bar(main_layout)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def _setup_header(self, main_layout):
        """Erstellt den Header-Bereich mit Titel und Logo."""
        header_layout = QVBoxLayout()
        
        # Titel
        title_label = QLabel("<h2><i>CNC-Konverter</i></h2>")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Logo
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

        # Logo rechts ausrichten
        logo_row = QHBoxLayout()
        logo_row.addStretch()
        logo_row.addWidget(logo_label)

        header_layout.addWidget(title_label)
        header_layout.addLayout(logo_row)
        main_layout.addLayout(header_layout)

    def _setup_main_grid(self, main_layout):
        """Erstellt das Haupt-Grid mit den drei Bereichen."""
        grid = QGridLayout()
        grid.setHorizontalSpacing(40)
        grid.setVerticalSpacing(5)  # Reduzierter Abstand für kompakteres Layout

        # Drei Hauptbereiche hinzufügen (Spalten 0, 2, 4 für Abstand)
        self.source_section.create_section(grid, 0)      # Quellverzeichnis
        self.converter_section.create_section(grid, 2)   # Konverter-Verzeichnis  
        self.target_section.create_section(grid, 4)      # Zielverzeichnis

        main_layout.addLayout(grid)
        
        # Zusätzlicher Abstand am unteren Rand
        main_layout.addStretch()

    def _setup_button_bar(self, main_layout):
        """Erstellt die untere Button-Leiste."""
        btn_layout = QHBoxLayout()
        
        # Reset-Button links
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self._reset_config)
        
        # Konvertierungs-Buttons rechts
        self.start_btn = QPushButton("Start Konvertierung")
        self.abort_btn = QPushButton("Abbruch")
        self.exit_btn = QPushButton("Beenden")
        self.exit_btn.clicked.connect(self.close)
        self.start_btn.clicked.connect(self.start_conversion)

        btn_layout.addWidget(self.reset_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.abort_btn)
        btn_layout.addWidget(self.exit_btn)
        main_layout.addLayout(btn_layout)

    # ----------------- Batch-Modus Umschalter -----------------
    def _toggle_batch_mode(self, state):
        """Wechselt zwischen Einzeldatei- und Batch-Konvertierungsmodus."""
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
                self.active_src_file.setPlaceholderText("Kein Quellfile ausgewaehlt")

    # ----------------- Backend-Integration -----------------
    def _validate_settings(self) -> tuple[bool, list[str]]:
        """Validiert alle Einstellungen mit dem umfassenden Validation-Modul."""
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
        """Startet die Konvertierung mit Progress-Dialog und Validierung."""
        try:
            self.logger.info("Konvertierung angefordert vom Benutzer")
            
            # Alle Einstellungen validieren
            is_valid, errors = self._validate_settings()
            if not is_valid:
                error_text = "\n• ".join(["Folgende Fehler müssen behoben werden:"] + errors)
                QMessageBox.critical(self, "Validierungsfehler", error_text)
                self.logger.warning(f"Validierung fehlgeschlagen: {len(errors)} Fehler")
                return

            # Alle Parameter für die Konvertierung sammeln
            conversion_params = self._gather_conversion_parameters()
            
            # Progress-Dialog erstellen und anzeigen
            title = "Batch-Konvertierung läuft..." if self.chk_convert_all.isChecked() else "Datei wird konvertiert..."
            progress_dialog = ProgressDialog(self, title)
            
            # Konvertierung im Progress-Dialog starten
            if self.chk_convert_all.isChecked():
                progress_dialog.start_conversion(self._run_batch_conversion, **conversion_params)
            else:
                progress_dialog.start_conversion(self._run_single_conversion, **conversion_params)
            
            # Dialog modal anzeigen
            result = progress_dialog.exec()
            
            # Nach Abschluss: Ziel-View aktualisieren
            if result == QDialog.DialogCode.Accepted:
                self._refresh_target_view()
                
        except Exception as e:
            error_msg = f"Unerwarteter Fehler beim Starten der Konvertierung: {str(e)}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "Fehler", error_msg)

    def _gather_conversion_parameters(self) -> dict:
        """Sammelt alle Parameter für die Konvertierung aus der UI."""
        target_dir = self.config.get("target_dir", "")
        excel_path = self.config["excel_path"]
        
        # Bei Batch-Modus: ListView-Pfad als Quellverzeichnis verwenden
        if self.chk_convert_all.isChecked():
            source_dir = self.current_source_listview_path or self.config.get("source_dir", "")
        else:
            source_dir = self.config.get("source_dir", "")
        
        # Dateiendungen aus allen Eingabefeldern sammeln (auch leere)
        file_endings = []
        for i in range(3):
            source_end = self.endings_q[i].text().strip()
            target_end = self.endings_z[i].text().strip()
            # Immer alle 3 Paare sammeln, auch wenn sie leer sind
            file_endings.append({"source": source_end, "target": target_end})

        # Alle Parameter in einem Dictionary zusammenfassen
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
        """Führt Batch-Konvertierung aller Dateien im Quellverzeichnis aus."""
        # Excel-Regeln für die Konvertierung laden
        rules = load_rules_from_excel(excel_path)
        self.logger.info(f"Excel-Regeln geladen: {len(rules)} Einträge")
        
        # Batch-Konvertierung mit allen Parametern starten
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
        """Führt Einzeldatei-Konvertierung der ausgewählten Quelldatei aus."""
        # Excel-Regeln für die Konvertierung laden
        rules = load_rules_from_excel(excel_path)
        self.logger.info(f"Excel-Regeln geladen: {len(rules)} Einträge")
        
        # Einzeldatei-Konvertierung mit allen Parametern
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
        
        # Pfad der konvertierten Datei für spätere Verwendung speichern
        self.last_converted_file = result_path
        return {'success': 1, 'failed': 0, 'total': 1}

    def _refresh_target_view(self):
        """Aktualisiert die Ziel-Verzeichnis-Ansicht nach der Konvertierung."""
        path = self.config.get("target_dir", "")
        if path and os.path.isdir(path):
            self.dst_explorer.refresh(path)
    
    def closeEvent(self, event):
        """Behandelt das Schließen der Anwendung mit Logging."""
        # Konfiguration vor dem Beenden speichern
        save_config(self.config)
        self.logger.info("=== CNC-Konverter beendet ===")
        event.accept()

    def _reset_config(self):
        """Setzt alle Eingabewerte und Config-Werte (außer Verzeichnispfade) zurück."""
        self.logger.info("Konfiguration zurückgesetzt.")
        
        # Alle UI-Elemente auf Standardwerte zurücksetzen
        self.src_prefix_count.setCurrentText("0")
        self.chk_src_spec.setChecked(False)
        self.src_prefix_str.clear()
        
        self.dst_prefix_count.setCurrentText("0")
        self.chk_dst_spec.setChecked(False)
        self.dst_prefix_str.setText("")  # Standardwert
        
        # Dateiendungen leeren
        for i in range(3):
            self.endings_q[i].clear()
            self.endings_z[i].clear()
        
        # Batch-Modus zurücksetzen
        self.chk_convert_all.setChecked(False)
        self.active_src_file.clear()
        self.active_src_file.setPlaceholderText("Kein Quellfile ausgewaehlt")
        self.active_src_file.setEnabled(True)
        
        # Aktive Dateien zurücksetzen
        self.active_src_file.clear()
        self.active_conv_file.clear()
        
        # Config auf Standardwerte zurücksetzen (außer Verzeichnispfade)
        self.config["source_prefix_count"] = 0
        self.config["source_prefix_specific"] = False
        self.config["source_prefix_string"] = ""
        self.config["target_prefix_count"] = 0
        self.config["target_prefix_specific"] = False
        self.config["target_prefix_string"] = ""
        self.config["file_endings"] = [
            {"source": "", "target": ""},
            {"source": "", "target": ""},
            {"source": "", "target": ""}
        ]
        self.config["active_source_file"] = ""
        self.config["excel_path"] = ""
        
        # Config wird beim Schließen gespeichert
        self.logger.info("Alle Eingabewerte zurückgesetzt.")
        QMessageBox.information(self, "Konfiguration zurückgesetzt", 
                              "Alle Eingabewerte wurden auf Standardwerte zurückgesetzt.\nVerzeichnispfade bleiben unverändert.")
