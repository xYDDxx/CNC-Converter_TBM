import os
import subprocess
import platform
from PyQt6.QtWidgets import QMessageBox


class FileOpener:
    """Verwaltet das Öffnen von Dateien in verschiedenen Editoren."""
    
    def __init__(self, parent):
        self.parent = parent
    
    def open_file_in_editor(self, section: str):
        """Öffnet die entsprechende Datei im passenden Editor je nach Bereich."""
        file_path = ""
        
        if section == "source":
            # Ausgewählte Quelldatei öffnen
            active_src = self.parent.config.get("active_source_file", "")
            if active_src and os.path.isfile(active_src):
                file_path = active_src
            else:
                QMessageBox.information(self.parent, "Hinweis", "Keine Quelldatei ausgewaehlt.")
                return
            self._open_in_text_editor(file_path)
                
        elif section == "converter":
            # Excel-Datei öffnen
            excel_path = self.parent.config.get("excel_path", "")
            if excel_path and os.path.isfile(excel_path):
                file_path = excel_path
            else:
                QMessageBox.information(self.parent, "Hinweis", "Keine Excel-Datei ausgewaehlt.")
                return
            self._open_in_excel(file_path)
                
        elif section == "target":
            # Zuerst prüfen ob im ListView eine Datei ausgewählt ist
            selected_indexes = self.parent.dst_explorer.list_view.selectedIndexes()
            if selected_indexes:
                model = self.parent.dst_explorer.list_view.model()
                selected_path = model.filePath(selected_indexes[0])
                if os.path.isfile(selected_path):
                    file_path = selected_path
            
            # Falls keine ListView-Auswahl, dann letztes konvertiertes File
            if not file_path and self.parent.last_converted_file and os.path.isfile(self.parent.last_converted_file):
                file_path = self.parent.last_converted_file
            
            if file_path:
                self._open_in_text_editor(file_path)
            else:
                QMessageBox.information(self.parent, "Hinweis", "Keine Zieldatei verfuegbar.")

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
            QMessageBox.warning(self.parent, "Fehler", f"Datei konnte nicht geoeffnet werden:\n{str(e)}")

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
            QMessageBox.warning(self.parent, "Fehler", f"Excel-Datei konnte nicht geoeffnet werden:\n{str(e)}")
