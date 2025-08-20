import json
import os

DEFAULT_CONFIG = {
    "excel_path": "./data/convert_table.xlsx",
    "source_dir": "./input",
    "target_dir": "./output",
    "cut_prefix": "",
    "add_prefix": "_Z",
    "new_ext": ".ZNC"
}

CONFIG_FILE = "./config.json"


def load_config() -> dict:
    """Lädt Konfiguration aus config.json oder erstellt Standardwerte."""
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠ Fehler beim Laden von config.json: {e}")
        return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    """Speichert Konfiguration nach config.json."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    print("💾 Konfiguration gespeichert.")


def update_config(key: str, value):
    """Setzt einen einzelnen Wert in der config.json."""
    config = load_config()
    config[key] = value
    save_config(config)
