from PyQt6.QtWidgets import QLabel, QPushButton, QLineEdit, QCheckBox, QComboBox, QHBoxLayout


class TargetSection:
    """Erstellt den Zielverzeichnis-Bereich mit Ausgabe-Einstellungen."""
    
    def __init__(self, parent):
        self.parent = parent
    
    def create_section(self, grid, col_start):
        """Erstellt den Zielverzeichnis-Bereich."""
        grid.addWidget(QLabel("Zielverzeichnis"), 0, col_start, 1, 2)

        # Pfad-Auswahl und Z-File-Öffnen-Button
        path_layout = QHBoxLayout()
        
        self.parent.dst_dir_field = QPushButton()
        self.parent.dst_dir_field.setText(self.parent.config.get("target_dir", "Pfad zum Zielverzeichnis auswaehlen..."))
        
        self.parent.dst_dir_field.clicked.connect(lambda: self.parent.directory_selector.select_directory("target"))
        
        self.parent.dst_open_btn = QPushButton("Z-File-oeffnen")
        self.parent.dst_open_btn.clicked.connect(lambda: self.parent.file_opener.open_file_in_editor("target"))
        self.parent.dst_open_btn.setFixedWidth(self.parent.dst_open_btn.sizeHint().width())
        
        path_layout.addWidget(self.parent.dst_dir_field)
        path_layout.addWidget(self.parent.dst_open_btn)
        
        grid.addLayout(path_layout, 1, col_start, 1, 2)

        # Datei-Explorer für Zielverzeichnis
        self.parent.dst_explorer = self.parent.file_explorer_factory.create_explorer("target")
        pair_layout = QHBoxLayout()
        pair_layout.setSpacing(5)
        self.parent.dst_explorer.tree.setFixedHeight(400)
        self.parent.dst_explorer.list_view.setFixedHeight(400)
        pair_layout.addWidget(self.parent.dst_explorer.tree)
        pair_layout.addWidget(self.parent.dst_explorer.list_view)
        grid.addLayout(pair_layout, 2, col_start, 1, 2)

        # Ziel-Praefix-Einstellungen
        grid.addWidget(QLabel("Ziel-Dateinamen-Praefix anhaengen"), 4, col_start, 1, 2)
        grid.addWidget(QLabel("Anzahl Zeichen"), 5, col_start)
        self.parent.dst_prefix_count = QComboBox()
        self.parent.dst_prefix_count.addItems([str(i) for i in range(0, 11)])
        self.parent.dst_prefix_count.currentTextChanged.connect(self.parent.config_manager.save_prefix_settings)
        grid.addWidget(self.parent.dst_prefix_count, 5, col_start + 1)
        
        self.parent.chk_dst_spec = QCheckBox("Nur-Spezif-String")
        self.parent.chk_dst_spec.stateChanged.connect(self.parent.config_manager.save_prefix_settings)
        grid.addWidget(self.parent.chk_dst_spec, 6, col_start)
        
        self.parent.dst_prefix_str = QLineEdit()
        self.parent.dst_prefix_str.setPlaceholderText("Praefix-String-Z")
        self.parent.dst_prefix_str.textChanged.connect(self.parent.config_manager.save_prefix_settings)
        grid.addWidget(self.parent.dst_prefix_str, 6, col_start + 1)
