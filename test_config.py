from logic.config_handler import load_config, update_config
from logic.excel_rules import load_rules_from_excel
from logic.converter import batch_convert

# Konfiguration laden
config = load_config()
print("🔧 Aktuelle Konfiguration:", config)

# Excel-Regeln laden
rules = load_rules_from_excel(config["excel_path"])

# Batch-Konvertierung mit Werten aus config.json
batch_convert(
    config["source_dir"],
    config["target_dir"],
    rules,
    cut_prefix=config["cut_prefix"],
    add_prefix=config["add_prefix"],
    new_ext=config["new_ext"]
)

# Beispiel: Quellordner ändern und speichern
update_config("source_dir", "./neuer_input_ordner")
