import os
from logic.excel_rules import load_rules_from_excel
from logic.file_handler import load_cnc_file, apply_rules_to_cnc, save_cnc_file, check_conversion

def convert_single_file(file_path: str, target_dir: str, rules: dict,
                        cut_prefix: str = "", add_prefix: str = "", new_ext: str | None = None):
    lines = load_cnc_file(file_path)
    converted = apply_rules_to_cnc(lines, rules)

    base = os.path.basename(file_path)
    name, ext = os.path.splitext(base)

    if cut_prefix and name.startswith(cut_prefix):
        name = name[len(cut_prefix):]
    if add_prefix:
        name = add_prefix + name
    if new_ext is not None:
        ext = new_ext

    out_path = os.path.join(target_dir, name + ext)
    save_cnc_file(converted, out_path)
    check_conversion(converted, rules)
    print(f"Konvertiert: {file_path} -> {out_path}")
