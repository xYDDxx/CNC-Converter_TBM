import json
import os

# Standard-Konfiguration mit allen verfügbaren Einstellungen
DEFAULT_CONFIG = {
    "excel_path": "./data/convert_table.xlsx",
    "source_dir": "./input",
    "target_dir": "./output",
    "converter_dir": "./data",
    "active_source_file": "",
    
    # Präfix-Handling für Dateinamen
    "source_prefix_count": 0,
    "source_prefix_specific": False,
    "source_prefix_string": "",
    "target_prefix_count": 0,
    "target_prefix_specific": False,
    "target_prefix_string": "",
    
    # Dateiendungen-Mapping von Quelle zu Ziel
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
            
            # Sicherstellen dass alle Standard-Schlüssel existieren
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
        # Sicherstellen dass alle Standard-Schlüssel vorhanden sind
        for key, default_value in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = default_value
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        print(f"💾 Konfiguration gespeichert: {len(config)} Schlüssel")
    except Exception as e:
        print(f"❌ Fehler beim Speichern der Konfiguration: {e}")


def update_config(key: str, value, config_dict: dict = None):
    """Setzt einen einzelnen Wert in der config.json und speichert sofort.
    
    Args:
        key: Der zu aktualisierende Schlüssel
        value: Der neue Wert
        config_dict: Optional: Bestehende Konfiguration (vermeidet doppeltes Laden)
    """
    if config_dict is None:
        # Nur laden wenn keine Konfiguration übergeben wurde
        config_dict = load_config()
    
    config_dict[key] = value
    save_config(config_dict)
    return config_dict