import os
from PyQt6.QtWidgets import QLabel, QPushButton, QLineEdit, QCheckBox, QComboBox, QHBoxLayout


class SourceSection:
    """Erstellt den Quellverzeichnis-Bereich mit allen UI-Elementen."""
    
    def __init__(self, parent):
        self.parent = parent
    
    def create_section(self, grid, col_start):
        """Erstellt den Quellverzeichnis-Bereich."""
        grid.addWidget(QLabel("Quellverzeichnis"), 0, col_start, 1, 2)

        # Pfad-Auswahl und Datei-Öffnen-Button
        path_layout = QHBoxLayout()
        
        self.parent.src_dir_field = QPushButton()  # Button statt LineEdit für bessere UX
        self.parent.src_dir_field.setText(self.parent.config.get("source_dir", "Pfad zum Quellverzeichnis auswaehlen..."))
       
        self.parent.src_dir_field.clicked.connect(lambda: self.parent.directory_selector.select_directory("source"))
        
        self.parent.src_open_btn = QPushButton("Q-File-oeffnen")
        self.parent.src_open_btn.clicked.connect(lambda: self.parent.file_opener.open_file_in_editor("source"))
        self.parent.src_open_btn.setFixedWidth(self.parent.src_open_btn.sizeHint().width())
        
        path_layout.addWidget(self.parent.src_dir_field)
        path_layout.addWidget(self.parent.src_open_btn)
        
        grid.addLayout(path_layout, 1, col_start, 1, 2)

        # Datei-Explorer (Tree + List)
        self.parent.src_explorer = self.parent.file_explorer_factory.create_explorer("source")
        pair_layout = QHBoxLayout()
        pair_layout.setSpacing(5)
        self.parent.src_explorer.tree.setFixedHeight(400)
        self.parent.src_explorer.list_view.setFixedHeight(400)
        pair_layout.addWidget(self.parent.src_explorer.tree)
        pair_layout.addWidget(self.parent.src_explorer.list_view)
        grid.addLayout(pair_layout, 2, col_start, 1, 2)

        # Batch-Konvertierung Checkbox
        self.parent.chk_convert_all = QCheckBox("Konvertiere Alle")
        self.parent.chk_convert_all.stateChanged.connect(self.parent._toggle_batch_mode)
        grid.addWidget(self.parent.chk_convert_all, 3, col_start)

        # Aktives Quellfile anzeigen
        grid.addWidget(QLabel("Akt. Aktives Quellfile"), 4, col_start, 1, 2)
        self.parent.active_src_file = QLineEdit()
        self.parent.active_src_file.setPlaceholderText("Kein Quellfile ausgewaehlt")
        self.parent.active_src_file.setReadOnly(True)
        grid.addWidget(self.parent.active_src_file, 5, col_start, 1, 2)

        # Quell-Praefix-Einstellungen
        grid.addWidget(QLabel("Quell-Dateinamen-Praefix abschneiden"), 6, col_start, 1, 2)
        grid.addWidget(QLabel("Anzahl Zeichen"), 7, col_start)
        self.parent.src_prefix_count = QComboBox()
        self.parent.src_prefix_count.addItems([str(i) for i in range(0, 11)])
        self.parent.src_prefix_count.currentTextChanged.connect(self.parent.config_manager.save_prefix_settings)
        grid.addWidget(self.parent.src_prefix_count, 7, col_start + 1)
        
        self.parent.chk_src_spec = QCheckBox("Nur-Spezif-String")
        self.parent.chk_src_spec.stateChanged.connect(self.parent.config_manager.save_prefix_settings)
        grid.addWidget(self.parent.chk_src_spec, 8, col_start)
        
        self.parent.src_prefix_str = QLineEdit()
        self.parent.src_prefix_str.setPlaceholderText("Praefix-String-Q")
        self.parent.src_prefix_str.textChanged.connect(self.parent.config_manager.save_prefix_settings)
        grid.addWidget(self.parent.src_prefix_str, 8, col_start + 1)
