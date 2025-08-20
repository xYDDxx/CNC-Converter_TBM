import os
from logic.excel_rules import load_rules_from_excel
from logic.file_handler import load_cnc_file, apply_rules_to_cnc, save_cnc_file, check_conversion

def convert_single_file(file_path: str, target_dir: str, rules: dict,
                        cut_prefix: str = "", add_prefix: str = "", new_ext: str | None = None):
    """
    Konvertiert eine einzelne Datei anhand der Regeln und speichert sie im Zielordner.
    """
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
    print(f"✅ Konvertiert: {file_path} -> {out_path}")


def batch_convert(source_dir: str, target_dir: str, rules: dict,
                  cut_prefix: str = "", add_prefix: str = "", new_ext: str | None = None):
    """
    Konvertiert alle Dateien im Quellordner (egal welche Endung) und speichert sie im Zielordner.
    """
    if not os.path.exists(source_dir):
        raise FileNotFoundError(f"Quellordner nicht gefunden: {source_dir}")
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)

    files = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]
    if not files:
        print("⚠ Keine Dateien im Quellordner gefunden.")
        return

    print(f"🔄 Starte Batch-Konvertierung: {len(files)} Dateien aus '{source_dir}' -> '{target_dir}'")

    success, failed = 0, 0
    for f in files:
        file_path = os.path.join(source_dir, f)
        try:
            convert_single_file(file_path, target_dir, rules,
                                cut_prefix=cut_prefix, add_prefix=add_prefix, new_ext=new_ext)
            success += 1
        except Exception as e:
            print(f"❌ Fehler bei {f}: {e}")
            failed += 1

    print(f"\n📊 Batch-Ergebnis: {success} erfolgreich, {failed} fehlgeschlagen.")
