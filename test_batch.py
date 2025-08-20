from logic.excel_rules import load_rules_from_excel
from logic.converter import batch_convert

rules = load_rules_from_excel("./data/convert_table.xlsx")

# Batch: alle Dateien aus ./input -> ./output
batch_convert("./input", "./output", rules, cut_prefix="", add_prefix="_Z", new_ext=".ZNC")
