from logic.excel_rules import load_rules_from_excel
from logic.converter import convert_single_file

rules = load_rules_from_excel("./data/convert_table.xlsx")
convert_single_file("./test_input.dnc", "./output", rules,
                    cut_prefix="", add_prefix="_Z", new_ext=".ZNC")
