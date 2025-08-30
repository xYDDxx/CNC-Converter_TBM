import json
import os

# Standard-Konfiguration mit allen verfügbaren Einstellungen
DEFAULT_CONFIG = {
    "excel_path": "./data/convert_table.xlsx",  # Excel-Konverterdatei
    "source_dir": "./input",                    # Quellverzeichnis
    "target_dir": "./output",                   # Zielverzeichnis
    "converter_dir": "./data",                  # Konverter-Verzeichnis
    "active_source_file": "",                   # Aktive Quelldatei
    
    # Präfix-Handling für Dateinamen
    "source_prefix_count": 0,                   # Anzahl Zeichen vom Anfang entfernen
    "source_prefix_specific": False,            # Nur spezifischen String entfernen
    "source_prefix_string": "",                 # Spezifischer Quell-Präfix
    "target_prefix_count": 0,                   # Anzahl Zeichen für neuen Präfix
    "target_prefix_specific": False,            # Nur bei spezifischem Quell-Präfix
    "target_prefix_string": "",                 # Neuer Ziel-Präfix
    
    # Dateiendungen-Mapping von Quelle zu Ziel (3 Paare)
    "file_endings": [
        {"source": "", "target": ""},
        {"source": "", "target": ""},
        {"source": "", "target": ""}
    ]
}

CONFIG_FILE = "./config.json"


def load_config() -> dict:
    """Lädt Konfiguration aus config.json oder erstellt Standardwerte."""
    if not os.path.exists(CONFIG_FILE):
        print("📁 Config-Datei nicht gefunden, erstelle Standardkonfiguration...")
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            
            # Sicherstellen dass alle Standard-Schlüssel existieren (Backward Compatibility)
            missing_keys = []
            for key, default_value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = default_value
                    missing_keys.append(key)
                elif key == "file_endings" and len(config[key]) < 3:
                    # Sicherstellen dass immer 3 Dateiendungs-Paare vorhanden sind
                    while len(config[key]) < 3:
                        config[key].append({"source": "", "target": ""})
                    missing_keys.append(f"{key} (auf 3 Paare erweitert)")
            
            # Debug-Ausgabe nur bei fehlenden Schlüsseln
            if missing_keys:
                print(f"⚠️ Fehlende Schlüssel ergänzt: {missing_keys}")
                # Konfiguration mit den ergänzten Werten speichern
                save_config(config)
            
            return config
    except Exception as e:
        print(f"⚠ Fehler beim Laden von config.json: {e}")
        print("🔄 Verwende Standardkonfiguration...")
        return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    """Speichert Konfiguration nach config.json mit Formatierung."""
    try:
        # Sicherstellen dass alle Standard-Schlüssel vorhanden sind (Vollständigkeit)
        for key, default_value in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = default_value
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        print(f"💾 Konfiguration gespeichert: {len(config)} Schlüssel")
    except Exception as e:
        print(f"❌ Fehler beim Speichern der Konfiguration: {e}")


