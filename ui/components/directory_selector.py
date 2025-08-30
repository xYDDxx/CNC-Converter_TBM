import os
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import QDir
from logic.logger import log_config_change


class DirectorySelector:
    """Verwaltet die Verzeichnis-Auswahl für alle Bereiche."""
    
    def __init__(self, parent):
        self.parent = parent
    
    def select_directory(self, section: str):
        """Öffnet den Dateidialog zur Pfad-Auswahl mit Validierung."""
        current_path = ""
        if section == "source":
            current_path = self.parent.config.get("source_dir", "")
        elif section == "converter":
            current_path = self.parent.config.get("converter_dir", "")
        elif section == "target":
            current_path = self.parent.config.get("target_dir", "")
        
        directory = QFileDialog.getExistingDirectory(
            self.parent, "Verzeichnis auswaehlen",
            current_path or QDir.homePath()
        )
        
        if directory:
            # Zusätzliche Validierung für Zielverzeichnis
            if section == "target":
                source_dir = self.parent.config.get("source_dir", "")
                if source_dir and os.path.samefile(directory, source_dir):
                    QMessageBox.warning(
                        self.parent, "Ungueltiges Verzeichnis", 
                        "Ziel- und Quellverzeichnis duerfen nicht identisch sein."
                    )
                    return
            
            # Button-Text und Config aktualisieren
            self._update_directory_config(section, directory)
            self._update_explorer_views(section, directory)

        self.parent.logger.info(f"Verzeichnis ausgewählt ({section}): {directory}")
    
    def _update_directory_config(self, section: str, directory: str):
        """Aktualisiert die Konfiguration für das ausgewählte Verzeichnis."""
        if section == "source":
            self.parent.src_dir_field.setText(directory)
            log_config_change("source_dir", self.parent.config.get("source_dir"), directory)
            self.parent.config["source_dir"] = directory
        elif section == "converter":
            self.parent.conv_dir_field.setText(directory)
            self.parent.config["converter_dir"] = directory
        elif section == "target":
            self.parent.dst_dir_field.setText(directory)
            self.parent.config["target_dir"] = directory
    
    def _update_explorer_views(self, section: str, directory: str):
        """Aktualisiert die Explorer-Views für das neue Verzeichnis."""
        if section == "source":
            self.parent.src_explorer.set_directory(directory)
            self.parent.current_source_listview_path = directory
        elif section == "converter":
            self.parent.conv_explorer.set_directory(directory)
            self.parent.current_converter_listview_path = directory
        elif section == "target":
            self.parent.dst_explorer.set_directory(directory)
            self.parent.current_target_listview_path = directory
