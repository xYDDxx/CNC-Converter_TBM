import os
from PyQt6.QtWidgets import QTreeView, QListView, QMessageBox
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtCore import QDir


class FileExplorer:
    """Erstellt einen Datei-Explorer mit Tree- und List-View."""
    
    def __init__(self, parent, section: str):
        self.parent = parent
        self.section = section
        self.tree, self.list_view = self._create_explorer()
    
    def _create_explorer(self):
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
                if self.section == "source":
                    self.parent.current_source_listview_path = path
                elif self.section == "converter":
                    self.parent.current_converter_listview_path = path
                elif self.section == "target":
                    self.parent.current_target_listview_path = path

        tree.clicked.connect(on_tree_clicked)

        def on_list_double_clicked(index):
            """Wird aufgerufen wenn eine Datei im List-View doppelgeklickt wird."""
            path = model.filePath(index)
            if not os.path.isfile(path):
                return

            if self.section == "source":
                # Quelldatei auswählen
                self.parent.active_src_file.setText(os.path.basename(path))
                self.parent.config["active_source_file"] = path
            elif self.section == "converter":
                # Excel-Datei auswählen (nur .xlsx/.xls)
                if path.lower().endswith((".xlsx", ".xls")):
                    self.parent.active_conv_file.setText(os.path.basename(path))
                    self.parent.config["excel_path"] = path
                else:
                    QMessageBox.information(
                        self.parent, "Hint",
                        "Bitte ein Excel-File (*.xlsx / *.xls) waehlen."
                    )

        list_view.doubleClicked.connect(on_list_double_clicked)
        return tree, list_view
    
    def set_directory(self, directory: str):
        """Setzt das aktuelle Verzeichnis für beide Views."""
        if directory and os.path.exists(directory):
            model = self.tree.model()
            self.tree.setRootIndex(model.index(directory))
            self.list_view.setRootIndex(model.index(directory))
    
    def refresh(self, directory: str):
        """Aktualisiert die Views für das angegebene Verzeichnis."""
        if directory and os.path.isdir(directory):
            model = self.tree.model()
            model.setRootPath(directory)
            self.tree.setRootIndex(model.index(directory))
            self.list_view.setRootIndex(model.index(directory))
