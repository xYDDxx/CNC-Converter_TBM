from PyQt6.QtWidgets import QLabel, QPushButton, QLineEdit, QHBoxLayout


class ConverterSection:
    """Erstellt den Konverter-Verzeichnis-Bereich mit Excel-Integration."""
    
    def __init__(self, parent):
        self.parent = parent
    
    def create_section(self, grid, col_start):
        """Erstellt den Konverter-Verzeichnis-Bereich."""
        grid.addWidget(QLabel("Konverter-Verzeichnis"), 0, col_start, 1, 2)

        # Pfad-Auswahl und Excel-Öffnen-Button
        path_layout = QHBoxLayout()
        
        self.parent.conv_dir_field = QPushButton()
        self.parent.conv_dir_field.setText(self.parent.config.get("converter_dir", "Pfad zum Konverter-Verzeichnis auswaehlen..."))
        
        self.parent.conv_dir_field.clicked.connect(lambda: self.parent.directory_selector.select_directory("converter"))
        
        self.parent.conv_open_btn = QPushButton("Excel-oeffnen")
        self.parent.conv_open_btn.clicked.connect(lambda: self.parent.file_opener.open_file_in_editor("converter"))
        self.parent.conv_open_btn.setFixedWidth(self.parent.conv_open_btn.sizeHint().width())
        
        path_layout.addWidget(self.parent.conv_dir_field)
        path_layout.addWidget(self.parent.conv_open_btn)
        
        grid.addLayout(path_layout, 1, col_start, 1, 2)

        # Datei-Explorer für Konverter-Verzeichnis
        self.parent.conv_explorer = self.parent.file_explorer_factory.create_explorer("converter")
        pair_layout = QHBoxLayout()
        pair_layout.setSpacing(5)
        self.parent.conv_explorer.tree.setFixedHeight(400)
        self.parent.conv_explorer.list_view.setFixedHeight(400)
        pair_layout.addWidget(self.parent.conv_explorer.tree)
        pair_layout.addWidget(self.parent.conv_explorer.list_view)
        grid.addLayout(pair_layout, 2, col_start, 1, 2)

        # Leere Zeile für einheitlichen Abstand (wie bei den anderen Bereichen)
        grid.addWidget(QLabel(""), 3, col_start, 1, 2)
        
        # Aktives Konverter-File anzeigen
        grid.addWidget(QLabel("Aktives Konverter-File"), 3, col_start, 1, 2)
        self.parent.active_conv_file = QLineEdit()
        self.parent.active_conv_file.setPlaceholderText("Kein Konverter-File ausgewaehlt")
        self.parent.active_conv_file.setReadOnly(True)
        grid.addWidget(self.parent.active_conv_file, 4, col_start, 1, 2)

        # Dateiendungen-Mapping Q -> Z
        grid.addWidget(QLabel("Datei Endungen Q -> Z"), 5, col_start, 1, 2)
        self.parent.endings_q = [QLineEdit() for _ in range(3)]
        self.parent.endings_z = [QLineEdit() for _ in range(3)]
        for i in range(3):
            self.parent.endings_q[i].setPlaceholderText(f"Q-End{i+1}")
            self.parent.endings_z[i].setPlaceholderText(f"Z-End{i+1}")
            self.parent.endings_q[i].textChanged.connect(self.parent.config_manager.save_ending_settings)
            self.parent.endings_z[i].textChanged.connect(self.parent.config_manager.save_ending_settings)
            grid.addWidget(self.parent.endings_q[i], 6 + i, col_start)
            grid.addWidget(self.parent.endings_z[i], 6 + i, col_start + 1)
