import os
from logic.excel_rules import load_rules_from_excel
from logic.file_handler import load_cnc_file, apply_rules_to_cnc, save_cnc_file, check_conversion, process_filename

def convert_single_file(file_path: str, target_dir: str, rules: dict,
                        source_prefix_count: int = 0,
                        source_prefix_specific: bool = False,
                        source_prefix_string: str = "",
                        target_prefix_count: int = 0,
                        target_prefix_specific: bool = False,
                        target_prefix_string: str = "",
                        file_endings: list = None):
    """
    Konvertiert eine einzelne Datei anhand der Regeln und speichert sie im Zielordner.
    """
    if file_endings is None:
        file_endings = []
        
    # CNC-Inhalt laden und konvertieren
    lines = load_cnc_file(file_path)
    converted = apply_rules_to_cnc(lines, rules)

    # Dateiname verarbeiten
    original_filename = os.path.basename(file_path)
    new_filename = process_filename(
        original_filename,
        source_prefix_count=source_prefix_count,
        source_prefix_specific=source_prefix_specific,
        source_prefix_string=source_prefix_string,
        target_prefix_count=target_prefix_count,
        target_prefix_specific=target_prefix_specific,
        target_prefix_string=target_prefix_string,
        file_endings=file_endings
    )

    # Datei speichern
    out_path = os.path.join(target_dir, new_filename)
    save_cnc_file(converted, out_path)
    check_conversion(converted, rules)
    print(f"✅ Konvertiert: {original_filename} -> {new_filename}")
    return out_path


def batch_convert(source_dir: str, target_dir: str, rules: dict,
                  source_prefix_count: int = 0,
                  source_prefix_specific: bool = False,
                  source_prefix_string: str = "",
                  target_prefix_count: int = 0,
                  target_prefix_specific: bool = False,
                  target_prefix_string: str = "",
                  file_endings: list = None):
    """
    Konvertiert alle Dateien im Quellordner (nur im aktuellen Ordner, NICHT in Unterordnern) 
    und speichert sie im Zielordner.
    """
    if file_endings is None:
        file_endings = []
        
    if not os.path.exists(source_dir):
        raise FileNotFoundError(f"Quellordner nicht gefunden: {source_dir}")
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)

    # Nur Dateien im aktuellen Ordner, KEINE Unterordner
    files = []
    try:
        for item in os.listdir(source_dir):
            item_path = os.path.join(source_dir, item)
            # Nur Dateien hinzufügen, keine Ordner
            if os.path.isfile(item_path):
                files.append(item)
    except Exception as e:
        raise Exception(f"Fehler beim Lesen des Quellordners: {e}")
    
    if not files:
        print("⚠ Keine Dateien im Quellordner gefunden.")
        return

    print(f"🔄 Starte Batch-Konvertierung: {len(files)} Dateien aus '{source_dir}' -> '{target_dir}'")
    print(f"📁 Nur Dateien im aktuellen Ordner werden konvertiert (keine Unterordner).")

    success, failed = 0, 0
    for f in files:
        file_path = os.path.join(source_dir, f)
        try:
            convert_single_file(
                file_path, target_dir, rules,
                source_prefix_count=source_prefix_count,
                source_prefix_specific=source_prefix_specific,
                source_prefix_string=source_prefix_string,
                target_prefix_count=target_prefix_count,
                target_prefix_specific=target_prefix_specific,
                target_prefix_string=target_prefix_string,
                file_endings=file_endings
            )
            success += 1
        except Exception as e:
            print(f"❌ Fehler bei {f}: {e}")
            failed += 1

    print(f"\n📊 Batch-Ergebnis: {success} erfolgreich, {failed} fehlgeschlagen.")