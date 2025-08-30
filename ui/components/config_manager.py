import os
from logic.logger import log_config_change


class ConfigManager:
    """Verwaltet das Laden und Speichern der Konfiguration in die UI."""
    
    def __init__(self, parent):
        self.parent = parent
    
    def load_config_to_ui(self):
        """Lädt die gespeicherte Konfiguration in alle UI-Elemente."""
        self.parent.logger.info("Lade Konfiguration in UI-Elemente...")
        
        # Flag setzen um zu verhindern dass _save_* Funktionen waehrend des Ladens getriggert werden
        self.parent._loading_config = True
        
        try:
            # Verzeichnispfade in Button-Texte setzen (Standardwerte falls nicht gesetzt)
            source_dir = self.parent.config.get("source_dir", "./input")
            converter_dir = self.parent.config.get("converter_dir", "./data")
            target_dir = self.parent.config.get("target_dir", "./output")
            
            self.parent.src_dir_field.setText(source_dir)
            self.parent.conv_dir_field.setText(converter_dir)
            self.parent.dst_dir_field.setText(target_dir)
            
            # Aktive Dateien in entsprechende Felder eintragen
            active_source = self.parent.config.get("active_source_file", "")
            excel_path = self.parent.config.get("excel_path", "")
            
            if active_source:
                self.parent.active_src_file.setText(os.path.basename(active_source))
            if excel_path:
                self.parent.active_conv_file.setText(os.path.basename(excel_path))

            # Praefix-Einstellungen in UI-Elemente laden (Quelle)
            src_prefix_count = self.parent.config.get("source_prefix_count", 0)
            src_prefix_specific = self.parent.config.get("source_prefix_specific", False)
            src_prefix_string = self.parent.config.get("source_prefix_string", "")
            
            self.parent.src_prefix_count.setCurrentText(str(src_prefix_count))
            self.parent.chk_src_spec.setChecked(src_prefix_specific)
            self.parent.src_prefix_str.setText(src_prefix_string)
            
            # Praefix-Einstellungen in UI-Elemente laden (Ziel)
            dst_prefix_count = self.parent.config.get("target_prefix_count", 0)
            dst_prefix_specific = self.parent.config.get("target_prefix_specific", False)
            dst_prefix_string = self.parent.config.get("target_prefix_string", "")
            
            self.parent.dst_prefix_count.setCurrentText(str(dst_prefix_count))
            self.parent.chk_dst_spec.setChecked(dst_prefix_specific)
            self.parent.dst_prefix_str.setText(dst_prefix_string)

            # Dateiendungen in Eingabefelder laden (mindestens 3 Paare)
            file_endings = self.parent.config.get("file_endings", [])
            while len(file_endings) < 3:
                file_endings.append({"source": "", "target": ""})
            
            for i in range(3):
                self.parent.endings_q[i].setText(file_endings[i].get("source", ""))
                self.parent.endings_z[i].setText(file_endings[i].get("target", ""))
            
            self.parent.logger.info("Alle Konfigurationswerte erfolgreich in UI geladen")
            
        finally:
            # Flag zurücksetzen
            self.parent._loading_config = False

    def save_prefix_settings(self):
        """Speichert alle aktuellen Praefix-Einstellungen in die Config mit Logging."""
        # Nicht speichern waehrend des initialen Ladens
        if hasattr(self.parent, '_loading_config') and self.parent._loading_config:
            return
            
        # Alle Präfix-Einstellungen sammeln
        config_updates = {
            "source_prefix_count": int(self.parent.src_prefix_count.currentText()),
            "source_prefix_specific": self.parent.chk_src_spec.isChecked(),
            "source_prefix_string": self.parent.src_prefix_str.text(),
            "target_prefix_count": int(self.parent.dst_prefix_count.currentText()),
            "target_prefix_specific": self.parent.chk_dst_spec.isChecked(),
            "target_prefix_string": self.parent.dst_prefix_str.text()
        }
        
        # Config aktualisieren mit Logging für geänderte Werte
        for key, value in config_updates.items():
            old_value = self.parent.config.get(key)
            if old_value != value:
                log_config_change(key, old_value, value)
            self.parent.config[key] = value

    def save_ending_settings(self):
        """Speichert die aktuellen Dateiendungs-Einstellungen in die Config."""
        # Nicht speichern waehrend des initialen Ladens
        if hasattr(self.parent, '_loading_config') and self.parent._loading_config:
            return
            
        # Dateiendungen aus allen Eingabefeldern sammeln
        file_endings = []
        for i in range(3):
            source_end = self.parent.endings_q[i].text().strip()
            target_end = self.parent.endings_z[i].text().strip()
            file_endings.append({"source": source_end, "target": target_end})
        
        # Config aktualisieren mit Logging
        old_value = self.parent.config.get("file_endings", [])
        if old_value != file_endings:
            log_config_change("file_endings", old_value, file_endings)
        self.parent.config["file_endings"] = file_endings

    def apply_initial_paths_to_views(self):
        """Wendet die gespeicherten Verzeichnispfade auf alle Explorer-Views an."""
        for config_key, explorer, attr in [
            ("source_dir", self.parent.src_explorer, "current_source_listview_path"),
            ("converter_dir", self.parent.conv_explorer, "current_converter_listview_path"),
            ("target_dir", self.parent.dst_explorer, "current_target_listview_path")
        ]:
            path = self.parent.config.get(config_key, "")
            if path and os.path.exists(path):
                explorer.set_directory(path)
                setattr(self.parent, attr, path)
