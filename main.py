import sys
import os
import subprocess
import platform
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QListView,
    QComboBox, QLineEdit, QCheckBox, QGridLayout, QHBoxLayout, QVBoxLayout,
    QFileDialog, QTreeView, QMessageBox, QDialog
)
from PyQt6.QtGui import QPixmap, QFileSystemModel, QPainter, QPen, QFont, QFontMetrics
from PyQt6.QtCore import Qt, QDir, QTimer

# Backend-Module importieren
from logic.config_handler import load_config, save_config
from logic.excel_rules import load_rules_from_excel
from logic.converter import convert_single_file, batch_convert
from logic.logger import setup_logger, get_logger, log_config_change
from logic.validation import comprehensive_validation
from progress_dialog import ProgressDialog


class SplashScreen(QWidget):
    """Splash Screen für den CNC-Konverter."""
    
    def __init__(self):
        super().__init__()
        
        # Vollbildmodus setzen
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        
        # Fenster-Eigenschaften
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        
        # Hintergrundfarbe auf Reinweiß setzen
        self.setStyleSheet("background-color: rgba(255,255,255,255);")
        
        # Logo-Pfad
        self.logo_path = os.path.join("img", "tbm_peening_controls_logo_Aufkleber.png")
        
        # Entwickler-Text
        self.developer_text = "Developed by Ian Felder"
    
    def paintEvent(self, event):
        """Überschreibt die Zeichenfunktion um Logo und Text zu zeichnen."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Logo laden und zentrieren
        logo_pixmap = QPixmap(self.logo_path)
        if not logo_pixmap.isNull():
            # Logo auf 400x200 skalieren
            scaled_logo = logo_pixmap.scaled(
                400, 200,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Logo in der Mitte zeichnen
            x = (self.width() - scaled_logo.width()) // 2
            y = (self.height() - scaled_logo.height()) // 2 - 50  # Etwas nach oben verschieben
            painter.drawPixmap(x, y, scaled_logo)
        
        # Entwickler-Text unten rechts zeichnen
        painter.setPen(QPen(Qt.GlobalColor.black))
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        
        # Text-Maße berechnen
        text_rect = painter.fontMetrics().boundingRect(self.developer_text)
        text_x = self.width() - text_rect.width() - 20
        text_y = self.height() - 20
        
        painter.drawText(text_x, text_y, self.developer_text)


class CNCConverterUI(QMainWindow):
    """Hauptfenster des CNC-Konverters mit vollständiger Benutzeroberfläche."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CNC-Konverter")
        self.setGeometry(200, 200, 1400, 800)

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
        
        # Benutzeroberfläche aufbauen
        self._setup_ui()
        
        # Initiale Konfiguration einmalig anwenden
        self._apply_initial_paths_to_views()
        self._load_config_to_ui()

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
        self.add_source_section(grid, 0)      # Quellverzeichnis
        self.add_converter_section(grid, 2)   # Konverter-Verzeichnis  
        self.add_target_section(grid, 4)      # Zielverzeichnis

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

    # ----------------- Abschnitte -----------------
    def add_source_section(self, grid, col_start):
        """Erstellt den Quellverzeichnis-Bereich mit allen UI-Elementen."""
        grid.addWidget(QLabel("Quellverzeichnis"), 0, col_start, 1, 2)

        # Pfad-Auswahl und Datei-Öffnen-Button
        path_layout = QHBoxLayout()
        
        self.src_dir_field = QPushButton()  # Button statt LineEdit für bessere UX
        self.src_dir_field.setText(self.config.get("source_dir", "Pfad zum Quellverzeichnis auswählen..."))
       
        self.src_dir_field.clicked.connect(lambda: self.select_directory_via_field("source"))
        
        self.src_open_btn = QPushButton("Q-File-öffnen")
        self.src_open_btn.clicked.connect(lambda: self.open_file_in_editor("source"))
        self.src_open_btn.setFixedWidth(self.src_open_btn.sizeHint().width())
        
        path_layout.addWidget(self.src_dir_field)
        path_layout.addWidget(self.src_open_btn)
        
        grid.addLayout(path_layout, 1, col_start, 1, 2)

        # Datei-Explorer (Tree + List)
        self.src_tree, self.src_list = self.create_explorer(section="source")
        pair_layout = QHBoxLayout()
        pair_layout.setSpacing(5)
        self.src_tree.setFixedHeight(400)
        self.src_list.setFixedHeight(400)
        pair_layout.addWidget(self.src_tree)
        pair_layout.addWidget(self.src_list)
        grid.addLayout(pair_layout, 2, col_start, 1, 2)

        # Batch-Konvertierung Checkbox
        self.chk_convert_all = QCheckBox("Konvertiere Alle")
        self.chk_convert_all.stateChanged.connect(self._toggle_batch_mode)
        grid.addWidget(self.chk_convert_all, 3, col_start)

        # Aktives Quellfile anzeigen
        grid.addWidget(QLabel("Akt. Aktives Quellfile"), 4, col_start, 1, 2)
        self.active_src_file = QLineEdit()
        self.active_src_file.setPlaceholderText("Kein Quellfile ausgewählt")
        self.active_src_file.setReadOnly(True)
        grid.addWidget(self.active_src_file, 5, col_start, 1, 2)

        # Quell-Präfix-Einstellungen
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
        """Erstellt den Konverter-Verzeichnis-Bereich mit Excel-Integration."""
        grid.addWidget(QLabel("Konverter-Verzeichnis"), 0, col_start, 1, 2)

        # Pfad-Auswahl und Excel-Öffnen-Button
        path_layout = QHBoxLayout()
        
        self.conv_dir_field = QPushButton()
        self.conv_dir_field.setText(self.config.get("converter_dir", "Pfad zum Konverter-Verzeichnis auswählen..."))
        
        self.conv_dir_field.clicked.connect(lambda: self.select_directory_via_field("converter"))
        
        self.conv_open_btn = QPushButton("Excel-öffnen")
        self.conv_open_btn.clicked.connect(lambda: self.open_file_in_editor("converter"))
        self.conv_open_btn.setFixedWidth(self.conv_open_btn.sizeHint().width())
        
        path_layout.addWidget(self.conv_dir_field)
        path_layout.addWidget(self.conv_open_btn)
        
        grid.addLayout(path_layout, 1, col_start, 1, 2)

        # Datei-Explorer für Konverter-Verzeichnis
        self.conv_tree, self.conv_list = self.create_explorer(section="converter")
        pair_layout = QHBoxLayout()
        pair_layout.setSpacing(5)
        self.conv_tree.setFixedHeight(400)
        self.conv_list.setFixedHeight(400)
        pair_layout.addWidget(self.conv_tree)
        pair_layout.addWidget(self.conv_list)
        grid.addLayout(pair_layout, 2, col_start, 1, 2)
# Leere Zeile für einheitlichen Abstand (wie bei den anderen Bereichen)
        grid.addWidget(QLabel(""), 3, col_start, 1, 2)
        # Aktives Konverter-File anzeigen
        grid.addWidget(QLabel("Aktives Konverter-File"), 3, col_start, 1, 2)
        self.active_conv_file = QLineEdit()
        self.active_conv_file.setPlaceholderText("Kein Konverter-File ausgewählt")
        self.active_conv_file.setReadOnly(True)
        grid.addWidget(self.active_conv_file, 4, col_start, 1, 2)

        # Dateiendungen-Mapping Q -> Z
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
        """Erstellt den Zielverzeichnis-Bereich mit Ausgabe-Einstellungen."""
        grid.addWidget(QLabel("Zielverzeichnis"), 0, col_start, 1, 2)

        # Pfad-Auswahl und Z-File-Öffnen-Button
        path_layout = QHBoxLayout()
        
        self.dst_dir_field = QPushButton()
        self.dst_dir_field.setText(self.config.get("target_dir", "Pfad zum Zielverzeichnis auswählen..."))
        
        self.dst_dir_field.clicked.connect(lambda: self.select_directory_via_field("target"))
        
        self.dst_open_btn = QPushButton("Z-File-öffnen")
        self.dst_open_btn.clicked.connect(lambda: self.open_file_in_editor("target"))
        self.dst_open_btn.setFixedWidth(self.dst_open_btn.sizeHint().width())
        
        path_layout.addWidget(self.dst_dir_field)
        path_layout.addWidget(self.dst_open_btn)
        
        grid.addLayout(path_layout, 1, col_start, 1, 2)

        # Datei-Explorer für Zielverzeichnis
        self.dst_tree, self.dst_list = self.create_explorer(section="target")
        pair_layout = QHBoxLayout()
        pair_layout.setSpacing(5)
        self.dst_tree.setFixedHeight(400)
        self.dst_list.setFixedHeight(400)
        pair_layout.addWidget(self.dst_tree)
        pair_layout.addWidget(self.dst_list)
        grid.addLayout(pair_layout, 2, col_start, 1, 2)


        # Ziel-Präfix-Einstellungen
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
        """Erstellt einen Datei-Explorer mit Tree- und List-View für den angegebenen Bereich."""
        # FileSystemModel für Datei-Explorer
        model = QFileSystemModel()
        model.setRootPath(QDir.rootPath())

        # Tree-View für Verzeichnisstruktur (links)
        tree = QTreeView()
        tree.setModel(model)
        tree.setRootIndex(model.index(QDir.rootPath()))
        tree.setColumnWidth(0, 150)
        tree.setHeaderHidden(True)

        # List-View für Dateien im ausgewählten Verzeichnis (rechts)
        list_view = QListView()
        list_view.setModel(model)

        def on_tree_clicked(index):
            """Wird aufgerufen wenn ein Verzeichnis im Tree-View geklickt wird."""
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
            """Wird aufgerufen wenn eine Datei im List-View doppelgeklickt wird."""
            path = model.filePath(index)
            if not os.path.isfile(path):
                return

            if section == "source":
                # Quelldatei auswählen
                self.active_src_file.setText(os.path.basename(path))
                self.config["active_source_file"] = path
            elif section == "converter":
                # Excel-Datei auswählen (nur .xlsx/.xls)
                if path.lower().endswith((".xlsx", ".xls")):
                    self.active_conv_file.setText(os.path.basename(path))
                    self.config["excel_path"] = path
                else:
                    QMessageBox.information(
                        self, "Hint",
                        "Bitte ein Excel-File (*.xlsx / *.xls) wählen."
                    )

        list_view.doubleClicked.connect(on_list_double_clicked)
        return tree, list_view

    # ----------------- Verzeichnis-Auswahl und Datei-Öffnung -----------------
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
                self.config["source_dir"] = directory
                model = self.src_tree.model()
                self.src_tree.setRootIndex(model.index(directory))
                self.src_list.setRootIndex(model.index(directory))
                self.current_source_listview_path = directory
            elif section == "converter":
                self.conv_dir_field.setText(directory)
                self.config["converter_dir"] = directory
                model = self.conv_tree.model()
                self.conv_tree.setRootIndex(model.index(directory))
                self.conv_list.setRootIndex(model.index(directory))
                self.current_converter_listview_path = directory
            elif section == "target":
                self.dst_dir_field.setText(directory)
                self.config["target_dir"] = directory
                model = self.dst_tree.model()
                self.dst_tree.setRootIndex(model.index(directory))
                self.dst_list.setRootIndex(model.index(directory))
                self.current_target_listview_path = directory

        self.logger.info(f"Verzeichnis ausgewählt ({section}): {directory}")

    def open_file_in_editor(self, section: str):
        """Öffnet die entsprechende Datei im passenden Editor je nach Bereich."""
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
        """Öffnet Datei in Notepad++ oder anderem Texteditor je nach Betriebssystem."""
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
                        # Nicht-blockierend starten mit subprocess.Popen
                        subprocess.Popen([npp_path, file_path], 
                                       creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, 'CREATE_NEW_CONSOLE') else 0)
                        return
                
                # Fallback: Windows Notepad
                subprocess.Popen(["notepad.exe", file_path], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, 'CREATE_NEW_CONSOLE') else 0)
            else:
                # Linux/Mac: Standard-Texteditor verwenden
                if system == "Darwin":  # macOS
                    subprocess.Popen(["open", "-t", file_path])
                else:  # Linux
                    subprocess.Popen(["xdg-open", file_path])
                    
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Datei konnte nicht geöffnet werden:\n{str(e)}")

    def _open_in_excel(self, file_path: str):
        """Öffnet Excel-Datei in Excel oder LibreOffice je nach Betriebssystem."""
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(file_path)  # Windows: Standard-Programm verwenden
            elif system == "Darwin":  # macOS
                subprocess.Popen(["open", file_path])
            else:  # Linux
                subprocess.Popen(["xdg-open", file_path])
                
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Excel-Datei konnte nicht geöffnet werden:\n{str(e)}")

    # ----------------- Config Management -----------------
    def _load_config_to_ui(self):
        """Lädt die gespeicherte Konfiguration in alle UI-Elemente."""
        self.logger.info("Lade Konfiguration in UI-Elemente...")
        
        # Flag setzen um zu verhindern dass _save_* Funktionen während des Ladens getriggert werden
        self._loading_config = True
        
        try:
            # Verzeichnispfade in Button-Texte setzen (Standardwerte falls nicht gesetzt)
            source_dir = self.config.get("source_dir", "./input")
            converter_dir = self.config.get("converter_dir", "./data")
            target_dir = self.config.get("target_dir", "./output")
            
            self.src_dir_field.setText(source_dir)
            self.conv_dir_field.setText(converter_dir)
            self.dst_dir_field.setText(target_dir)
            
            # Aktive Dateien in entsprechende Felder eintragen
            active_source = self.config.get("active_source_file", "")
            excel_path = self.config.get("excel_path", "")
            
            if active_source:
                self.active_src_file.setText(os.path.basename(active_source))
            if excel_path:
                self.active_conv_file.setText(os.path.basename(excel_path))

            # Präfix-Einstellungen in UI-Elemente laden (Quelle)
            src_prefix_count = self.config.get("source_prefix_count", 0)
            src_prefix_specific = self.config.get("source_prefix_specific", False)
            src_prefix_string = self.config.get("source_prefix_string", "")
            
            self.src_prefix_count.setCurrentText(str(src_prefix_count))
            self.chk_src_spec.setChecked(src_prefix_specific)
            self.src_prefix_str.setText(src_prefix_string)
            
            # Präfix-Einstellungen in UI-Elemente laden (Ziel)
            dst_prefix_count = self.config.get("target_prefix_count", 0)
            dst_prefix_specific = self.config.get("target_prefix_specific", False)
            dst_prefix_string = self.config.get("target_prefix_string", "")
            
            self.dst_prefix_count.setCurrentText(str(dst_prefix_count))
            self.chk_dst_spec.setChecked(dst_prefix_specific)
            self.dst_prefix_str.setText(dst_prefix_string)

            # Dateiendungen in Eingabefelder laden (mindestens 3 Paare)
            file_endings = self.config.get("file_endings", [])
            while len(file_endings) < 3:
                file_endings.append({"source": "", "target": ""})
            
            for i in range(3):
                self.endings_q[i].setText(file_endings[i].get("source", ""))
                self.endings_z[i].setText(file_endings[i].get("target", ""))
            
            self.logger.info("Alle Konfigurationswerte erfolgreich in UI geladen")
            
        finally:
            # Flag zurücksetzen
            self._loading_config = False

    def _save_prefix_settings(self):
        """Speichert alle aktuellen Präfix-Einstellungen in die Config mit Logging."""
        # Nicht speichern während des initialen Ladens
        if hasattr(self, '_loading_config') and self._loading_config:
            return
            
        # Alle Präfix-Einstellungen sammeln
        config_updates = {
            "source_prefix_count": int(self.src_prefix_count.currentText()),
            "source_prefix_specific": self.chk_src_spec.isChecked(),
            "source_prefix_string": self.src_prefix_str.text(),
            "target_prefix_count": int(self.dst_prefix_count.currentText()),
            "target_prefix_specific": self.chk_dst_spec.isChecked(),
            "target_prefix_string": self.dst_prefix_str.text()
        }
        
        # Config aktualisieren mit Logging für geänderte Werte
        for key, value in config_updates.items():
            old_value = self.config.get(key)
            if old_value != value:
                log_config_change(key, old_value, value)
            self.config[key] = value

    def _save_ending_settings(self):
        """Speichert die aktuellen Dateiendungs-Einstellungen in die Config."""
        # Nicht speichern während des initialen Ladens
        if hasattr(self, '_loading_config') and self._loading_config:
            return
            
        # Dateiendungen aus allen Eingabefeldern sammeln
        file_endings = []
        for i in range(3):
            source_end = self.endings_q[i].text().strip()
            target_end = self.endings_z[i].text().strip()
            file_endings.append({"source": source_end, "target": target_end})
        
        # Config aktualisieren mit Logging
        old_value = self.config.get("file_endings", [])
        if old_value != file_endings:
            log_config_change("file_endings", old_value, file_endings)
        self.config["file_endings"] = file_endings

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
                self.active_src_file.setPlaceholderText("Kein Quellfile ausgewählt")

    # ----------------- Backend-Integration -----------------
    def _apply_initial_paths_to_views(self):
        """Wendet die gespeicherten Verzeichnispfade auf alle Explorer-Views an."""
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
        model = self.dst_tree.model()
        path = self.config.get("target_dir", "")
        if path and os.path.isdir(path):
            # Model refresh erzwingen um neue Dateien anzuzeigen
            model.setRootPath(path)
            self.dst_tree.setRootIndex(model.index(path))
            self.dst_list.setRootIndex(model.index(path))
    
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
        self.active_src_file.setPlaceholderText("Kein Quellfile ausgewählt")
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Splash Screen anzeigen
    splash = SplashScreen()
    splash.show()
    
    # App verarbeiten
    app.processEvents()
    
    # Hauptfenster erstellen
    window = CNCConverterUI()
    
    # Splash Screen nach 2 Sekunden ausblenden und Hauptfenster anzeigen
    QTimer.singleShot(2000, lambda: (splash.close(), window.show()))
    
    sys.exit(app.exec())