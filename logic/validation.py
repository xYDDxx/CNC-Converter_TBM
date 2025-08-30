import os
from pathlib import Path
from typing import List, Tuple, Dict
from logic.logger import get_logger, log_validation_error


def validate_directories(source_dir: str, target_dir: str, converter_dir: str = None) -> Tuple[bool, List[str]]:
    """
    Validiert Quell-, Ziel- und Konverter-Verzeichnisse.
    
    Args:
        source_dir: Quellverzeichnis
        target_dir: Zielverzeichnis  
        converter_dir: Konverter-Verzeichnis (optional)
    
    Returns:
        (is_valid, error_list)
    """
    errors = []
    logger = get_logger()
    
    # Quellverzeichnis prüfen (muss existieren)
    if not source_dir or not source_dir.strip():
        errors.append("Quellverzeichnis ist nicht angegeben.")
    elif not os.path.exists(source_dir):
        errors.append(f"Quellverzeichnis existiert nicht: {source_dir}")
    elif not os.path.isdir(source_dir):
        errors.append(f"Quellverzeichnis ist keine gültige Ordner: {source_dir}")
    
    # Zielverzeichnis prüfen (wird erstellt falls nicht vorhanden)
    if not target_dir or not target_dir.strip():
        errors.append("Zielverzeichnis ist nicht angegeben.")
    else:
        # Zielverzeichnis erstellen falls es nicht existiert
        try:
            os.makedirs(target_dir, exist_ok=True)
        except Exception as e:
            errors.append(f"Zielverzeichnis kann nicht erstellt werden: {str(e)}")
    
    # Verzeichnisse dürfen nicht identisch sein (Sicherheit)
    if source_dir and target_dir:
        try:
            source_path = Path(source_dir).resolve()
            target_path = Path(target_dir).resolve()
            
            if source_path == target_path:
                errors.append("Quell- und Zielverzeichnis dürfen nicht identisch sein.")
                
        except Exception as e:
            logger.warning(f"Pfad-Vergleich fehlgeschlagen: {e}")
    
    # Konverter-Verzeichnis prüfen (falls angegeben)
    if converter_dir:
        if not os.path.exists(converter_dir):
            errors.append(f"Konverter-Verzeichnis existiert nicht: {converter_dir}")
        elif not os.path.isdir(converter_dir):
            errors.append(f"Konverter-Verzeichnis ist kein gültiger Ordner: {converter_dir}")
    
    if errors:
        log_validation_error(errors)
    
    return len(errors) == 0, errors


def validate_excel_file(excel_path: str) -> Tuple[bool, List[str]]:
    """
    Validiert die Excel-Konverterdatei.
    
    Args:
        excel_path: Pfad zur Excel-Datei
    
    Returns:
        (is_valid, error_list)
    """
    errors = []
    logger = get_logger()
    
    if not excel_path or not excel_path.strip():
        errors.append("Keine Excel-Konverterdatei ausgewählt.")
        return False, errors
    
    if not os.path.exists(excel_path):
        errors.append(f"Excel-Datei existiert nicht: {excel_path}")
        return False, errors
    
    if not os.path.isfile(excel_path):
        errors.append(f"Excel-Pfad ist keine Datei: {excel_path}")
        return False, errors
    
    # Dateiendung prüfen (.xlsx oder .xls)
    valid_extensions = ['.xlsx', '.xls']
    file_ext = os.path.splitext(excel_path)[1].lower()
    if file_ext not in valid_extensions:
        errors.append(f"Ungültige Dateiendung für Excel-Datei. Erwartet: {', '.join(valid_extensions)}, erhalten: {file_ext}")
        return False, errors
    
    # Excel-Datei laden und Inhalt prüfen
    try:
        import openpyxl
        wb = openpyxl.load_workbook(excel_path, data_only=True)
        sheet = wb.active
        
        # Mindestens eine Regel prüfen (ab Zeile 2, Header in Zeile 1)
        rule_count = 0
        for row in sheet.iter_rows(min_row=2, values_only=True):
            q = row[0]
            if q is not None and str(q).strip():
                rule_count += 1
                break
        
        if rule_count == 0:
            errors.append("Excel-Datei enthält keine gültigen Konvertierungsregeln.")
        else:
            logger.debug(f"Excel-Datei erfolgreich validiert: {excel_path}")
            
    except Exception as e:
        errors.append(f"Fehler beim Lesen der Excel-Datei: {str(e)}")
    
    if errors:
        log_validation_error(errors)
    
    return len(errors) == 0, errors


def validate_source_files(source_dir: str, batch_mode: bool, active_source_file: str = None) -> Tuple[bool, List[str]]:
    """
    Validiert Quell-Dateien je nach Modus.
    
    Args:
        source_dir: Quellverzeichnis
        batch_mode: True für Batch-Modus, False für Einzeldatei
        active_source_file: Aktive Quelldatei (für Einzelmodus)
    
    Returns:
        (is_valid, error_list)
    """
    errors = []
    logger = get_logger()
    
    if batch_mode:
        # Batch-Modus: Mindestens eine Datei im Quellverzeichnis (flache Struktur)
        if not os.path.isdir(source_dir):
            errors.append("Quellverzeichnis für Batch-Modus ungültig.")
            return False, errors
        
        try:
            files = [f for f in os.listdir(source_dir) 
                    if os.path.isfile(os.path.join(source_dir, f))]
            
            if not files:
                errors.append("Keine Dateien im Quellverzeichnis für Batch-Konvertierung gefunden.")
            else:
                logger.debug(f"Batch-Modus: {len(files)} Dateien für Konvertierung gefunden.")
                
        except Exception as e:
            errors.append(f"Fehler beim Lesen des Quellverzeichnisses: {str(e)}")
    
    else:
        # Einzeldatei-Modus: Spezifische Datei prüfen (muss existieren)
        if not active_source_file:
            errors.append("Für Einzeldatei-Konvertierung muss eine Quelldatei ausgewählt sein.")
        elif not os.path.exists(active_source_file):
            errors.append(f"Ausgewählte Quelldatei existiert nicht: {active_source_file}")
        elif not os.path.isfile(active_source_file):
            errors.append(f"Ausgewählte Quelle ist keine Datei: {active_source_file}")
        else:
            logger.debug(f"Einzeldatei-Modus: Datei validiert: {os.path.basename(active_source_file)}")
    
    if errors:
        log_validation_error(errors)
    
    return len(errors) == 0, errors


def validate_filename_settings(source_prefix_count: int, source_prefix_string: str,
                              target_prefix_count: int, target_prefix_string: str,
                              file_endings: List[Dict[str, str]]) -> Tuple[bool, List[str]]:
    """
    Validiert Dateinamen-Einstellungen (Präfixe und Endungen).
    
    Returns:
        (is_valid, error_list)
    """
    errors = []
    logger = get_logger()
    
    # Quell-Präfix validieren (Länge und Realismus)
    if source_prefix_count > 0:
        if source_prefix_string and len(source_prefix_string) != source_prefix_count:
            errors.append(f"Quell-Präfix '{source_prefix_string}' hat {len(source_prefix_string)} Zeichen, "
                         f"aber {source_prefix_count} erwartet.")
        elif source_prefix_count > 20:  # Sinnvolle Obergrenze
            errors.append(f"Quell-Präfix-Länge von {source_prefix_count} ist unrealistisch groß (max. 20).")
    
    # Ziel-Präfix validieren (Länge und Realismus)
    if target_prefix_count > 0:
        if target_prefix_string and len(target_prefix_string) != target_prefix_count:
            errors.append(f"Ziel-Präfix '{target_prefix_string}' hat {len(target_prefix_string)} Zeichen, "
                         f"aber {target_prefix_count} erwartet.")
        elif target_prefix_count > 20:  # Sinnvolle Obergrenze
            errors.append(f"Ziel-Präfix-Länge von {target_prefix_count} ist unrealistisch groß (max. 20).")
    
    # Dateiendungen validieren (Format und Länge)
    for i, mapping in enumerate(file_endings):
        if not mapping:
            continue
            
        source_end = mapping.get("source", "").strip()
        target_end = mapping.get("target", "").strip()
        
        # Skip leere Mappings
        if not source_end and not target_end:
            continue
            
        # Validierung nur wenn mindestens eines gesetzt ist
        if source_end:
            if not source_end.startswith("."):
                errors.append(f"Quell-Endung {i+1} '{source_end}' sollte mit '.' beginnen.")
            elif len(source_end) > 10:  # Sinnvolle Obergrenze
                errors.append(f"Quell-Endung {i+1} '{source_end}' ist zu lang (max. 10 Zeichen).")
        
        if target_end:
            if not target_end.startswith("."):
                errors.append(f"Ziel-Endung {i+1} '{target_end}' sollte mit '.' beginnen.")
            elif len(target_end) > 10:  # Sinnvolle Obergrenze
                errors.append(f"Ziel-Endung {i+1} '{target_end}' ist zu lang (max. 10 Zeichen).")
    
    if errors:
        log_validation_error(errors)
    else:
        logger.debug("Dateinamen-Einstellungen erfolgreich validiert.")
    
    return len(errors) == 0, errors


def validate_write_permissions(target_dir: str) -> Tuple[bool, List[str]]:
    """
    Prüft Schreibberechtigungen für das Zielverzeichnis.
    
    Args:
        target_dir: Zielverzeichnis
    
    Returns:
        (is_valid, error_list)
    """
    errors = []
    logger = get_logger()
    
    try:
        # Test-Datei schreiben (Schreibberechtigung prüfen)
        test_file = os.path.join(target_dir, ".write_test_cnc_converter")
        with open(test_file, 'w') as f:
            f.write("test")
        
        # Test-Datei löschen (Löschberechtigung prüfen)
        os.remove(test_file)
        logger.debug(f"Schreibberechtigung für Zielverzeichnis bestätigt: {target_dir}")
        
    except Exception as e:
        errors.append(f"Keine Schreibberechtigung für Zielverzeichnis: {str(e)}")
    
    if errors:
        log_validation_error(errors)
    
    return len(errors) == 0, errors


def comprehensive_validation(config: dict, batch_mode: bool) -> Tuple[bool, List[str]]:
    """
    Führt eine umfassende Validierung aller Einstellungen durch.
    
    Args:
        config: Konfigurationsdictionary
        batch_mode: True für Batch-Modus
    
    Returns:
        (is_valid, error_list)
    """
    all_errors = []
    logger = get_logger()
    
    logger.debug("=== Umfassende Validierung gestartet ===")
    
    # 1. Verzeichnisse validieren (Quelle, Ziel, Konverter)
    source_dir = config.get("source_dir", "")
    target_dir = config.get("target_dir", "")
    converter_dir = config.get("converter_dir", "")
    
    is_valid, errors = validate_directories(source_dir, target_dir, converter_dir)
    all_errors.extend(errors)
    
    # 2. Excel-Datei validieren (Pfad und Inhalt)
    excel_path = config.get("excel_path", "")
    is_valid, errors = validate_excel_file(excel_path)
    all_errors.extend(errors)
    
    # 3. Quelldateien validieren (je nach Modus)
    active_source_file = config.get("active_source_file", "")
    is_valid, errors = validate_source_files(source_dir, batch_mode, active_source_file)
    all_errors.extend(errors)
    
    # 4. Dateinamen-Einstellungen validieren (Präfixe und Endungen)
    file_endings = config.get("file_endings", [])
    is_valid, errors = validate_filename_settings(
        config.get("source_prefix_count", 0),
        config.get("source_prefix_string", ""),
        config.get("target_prefix_count", 0),
        config.get("target_prefix_string", ""),
        file_endings
    )
    all_errors.extend(errors)
    
    # 5. Schreibberechtigungen prüfen (Zielverzeichnis)
    if target_dir and os.path.exists(target_dir):
        is_valid, errors = validate_write_permissions(target_dir)
        all_errors.extend(errors)
    
    final_valid = len(all_errors) == 0
    
    if final_valid:
        logger.info("✅ Alle Validierungen erfolgreich bestanden.")
    else:
        logger.warning(f"⚠️ Validierung fehlgeschlagen: {len(all_errors)} Fehler gefunden.")
    
    return final_valid, all_errors