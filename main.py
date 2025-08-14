import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QListView,
    QComboBox, QLineEdit, QCheckBox, QGridLayout, QHBoxLayout, QVBoxLayout,
    QFileDialog, QTreeView
)
from PyQt6.QtGui import QPixmap, QFileSystemModel
from PyQt6.QtCore import Qt, QDir


class CNCConverterUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CNC-Konverter")
        self.setGeometry(200, 200, 1400, 800)

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
            scaled_pixmap = pixmap.scaled(200, 42, Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        logo_row = QHBoxLayout()
        logo_row.addStretch()
        logo_row.addWidget(logo_label)

        header_layout.addWidget(title_label)
        header_layout.addLayout(logo_row)
        main_layout.addLayout(header_layout)

        # Grid für Module mit größerem Abstand zwischen den Modulen
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

        btn_layout.addStretch()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.abort_btn)
        btn_layout.addWidget(self.exit_btn)
        main_layout.addLayout(btn_layout)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    # ----------------- Abschnitte -----------------
    def add_source_section(self, grid, col_start):
        grid.addWidget(QLabel("Quellverzeichnis"), 0, col_start, 1, 2)

        self.src_dir_field = QLineEdit()
        self.src_dir_field.setPlaceholderText("Pfad zum Quellverzeichnis...")
        self.src_dir_btn = QPushButton("Durchsuchen")
        self.src_dir_btn.clicked.connect(lambda: self.select_directory(self.src_dir_field, self.src_tree, self.src_list))
        grid.addWidget(self.src_dir_field, 1, col_start)
        grid.addWidget(self.src_dir_btn, 1, col_start + 1)

        self.src_tree, self.src_list = self.create_explorer()
        pair_layout = QHBoxLayout()
        pair_layout.setSpacing(5)
        self.src_tree.setFixedHeight(400)
        self.src_list.setFixedHeight(400)
        pair_layout.addWidget(self.src_tree)
        pair_layout.addWidget(self.src_list)
        grid.addLayout(pair_layout, 2, col_start, 1, 2)

        self.chk_convert_all = QCheckBox("Konvertiere Alle")
        grid.addWidget(self.chk_convert_all, 3, col_start)
        self.active_q_btn = QPushButton("Akt. Aktives Quellfile")
        grid.addWidget(self.active_q_btn, 3, col_start + 1)

        grid.addWidget(QLabel("Quell-Dateinamen-Präfix abschneiden"), 4, col_start, 1, 2)
        grid.addWidget(QLabel("Anzahl Zeichen"), 5, col_start)
        self.src_prefix_count = QComboBox()
        self.src_prefix_count.addItems([str(i) for i in range(0, 11)])
        grid.addWidget(self.src_prefix_count, 5, col_start + 1)
        self.chk_src_spec = QCheckBox("Nur-Spezif-String")
        grid.addWidget(self.chk_src_spec, 6, col_start)
        self.src_prefix_str = QLineEdit()
        self.src_prefix_str.setPlaceholderText("Präfix-String-Q")
        grid.addWidget(self.src_prefix_str, 6, col_start + 1)

    def add_converter_section(self, grid, col_start):
        grid.addWidget(QLabel("Konverter-Verzeichnis"), 0, col_start, 1, 2)

        self.conv_dir_field = QLineEdit()
        self.conv_dir_field.setPlaceholderText("Pfad zum Konverter-Verzeichnis...")
        self.conv_dir_btn = QPushButton("Durchsuchen")
        self.conv_dir_btn.clicked.connect(lambda: self.select_directory(self.conv_dir_field, self.conv_tree, self.conv_list))
        grid.addWidget(self.conv_dir_field, 1, col_start)
        grid.addWidget(self.conv_dir_btn, 1, col_start + 1)

        self.conv_tree, self.conv_list = self.create_explorer()
        pair_layout = QHBoxLayout()
        pair_layout.setSpacing(5)
        self.conv_tree.setFixedHeight(400)
        self.conv_list.setFixedHeight(400)
        pair_layout.addWidget(self.conv_tree)
        pair_layout.addWidget(self.conv_list)
        grid.addLayout(pair_layout, 2, col_start, 1, 2)

        # Neuer Abschnitt: Aktives Konverter-File
        grid.addWidget(QLabel("Aktives Konverter-File"), 3, col_start, 1, 2)
        self.active_conv_file = QLineEdit()
        self.active_conv_file.setPlaceholderText("Kein Konverter-File ausgewählt")
        self.active_conv_file.setReadOnly(True)
        grid.addWidget(self.active_conv_file, 4, col_start, 1, 2)

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

        self.dst_dir_field = QLineEdit()
        self.dst_dir_field.setPlaceholderText("Pfad zum Zielverzeichnis...")
        self.dst_dir_btn = QPushButton("Durchsuchen")
        self.dst_dir_btn.clicked.connect(lambda: self.select_directory(self.dst_dir_field, self.dst_tree, self.dst_list))
        grid.addWidget(self.dst_dir_field, 1, col_start)
        grid.addWidget(self.dst_dir_btn, 1, col_start + 1)

        self.dst_tree, self.dst_list = self.create_explorer()
        pair_layout = QHBoxLayout()
        pair_layout.setSpacing(5)
        self.dst_tree.setFixedHeight(400)
        self.dst_list.setFixedHeight(400)
        pair_layout.addWidget(self.dst_tree)
        pair_layout.addWidget(self.dst_list)
        grid.addLayout(pair_layout, 2, col_start, 1, 2)

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
    def create_explorer(self):
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
            list_view.setRootIndex(model.index(path))
            # Falls Konverter-Tree: Aktives File setzen
            if tree is self.conv_tree and os.path.isfile(path):
                self.active_conv_file.setText(os.path.basename(path))

        tree.clicked.connect(on_tree_clicked)
        return tree, list_view

    # ----------------- Backend Hook -----------------
    def select_directory(self, path_field, tree_view, list_view):
        directory = QFileDialog.getExistingDirectory(self, "Verzeichnis auswählen")
        if directory:
            path_field.setText(directory)
            model = tree_view.model()
            tree_view.setRootIndex(model.index(directory))
            list_view.setRootIndex(model.index(directory))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CNCConverterUI()
    window.show()
    sys.exit(app.exec())
