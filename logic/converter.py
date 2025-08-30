import os
from typing import Dict, List, Callable, Optional
from logic.file_handler import load_cnc_file, apply_rules_to_cnc, save_cnc_file, check_conversion, process_filename
from logic.logger import get_logger, log_conversion_start, log_conversion_success, log_conversion_error, log_batch_summary


def convert_single_file(file_path: str, target_dir: str, rules: dict,
                        source_prefix_count: int = 0,
                        source_prefix_specific: bool = False,
                        source_prefix_string: str = "",
                        target_prefix_count: int = 0,
                        target_prefix_specific: bool = False,
                        target_prefix_string: str = "",
                        file_endings: list = None,
                        progress_callback: Optional[Callable] = None,
                        cancel_check: Optional[Callable] = None) -> str:
    """
    Konvertiert eine einzelne Datei anhand der Regeln und speichert sie im Zielordner.
    
    Args:
        file_path: Pfad zur Quelldatei
        target_dir: Zielverzeichnis
        rules: Konvertierungsregeln aus Excel
        source_prefix_count: Anzahl Zeichen vom Anfang entfernen
        source_prefix_specific: Nur spezifischen String entfernen
        source_prefix_string: Spezifischer Quell-Praefix
        target_prefix_count: Anzahl Zeichen fuer neuen Praefix
        target_prefix_specific: Nur bei spezifischem Quell-Praefix
        target_prefix_string: Neuer Ziel-Praefix
        file_endings: Dateiendungs-Mappings
        progress_callback: Callback für Progress-Updates (current, total, filename, status)
        cancel_check: Callback zum Prüfen ob abgebrochen werden soll
    
    Returns:
        Pfad zur konvertierten Datei
        
    Raises:
        Exception: Bei Konvertierungsfehlern
    """
    logger = get_logger()
    
    if file_endings is None:
        file_endings = []
    
    # Abbruch-Check
    if cancel_check and cancel_check():
        raise Exception("Konvertierung abgebrochen")
    
    try:
        original_filename = os.path.basename(file_path)
        logger.debug(f"Starte Konvertierung: {original_filename}")
        
        # Progress-Update: Start
        if progress_callback:
            progress_callback(0, 1, file_path, f"Lade {original_filename}")
        
        # CNC-Inhalt laden und konvertieren
        lines = load_cnc_file(file_path)
        
        if cancel_check and cancel_check():
            raise Exception("Konvertierung abgebrochen")
        
        # Progress-Update: Konvertierung
        if progress_callback:
            progress_callback(0, 1, file_path, f"Konvertiere {original_filename}")
        
        # Regeln auf CNC-Inhalt anwenden
        converted = apply_rules_to_cnc(lines, rules)
        
        # Angewendete Regeln zählen (für Logging)
        applied_rules = count_applied_rules(lines, converted, rules)
        
        if cancel_check and cancel_check():
            raise Exception("Konvertierung abgebrochen")
        
        # Dateiname verarbeiten (Präfixe und Endungen)
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
        
        # Progress-Update: Speichern
        if progress_callback:
            progress_callback(0, 1, file_path, f"Speichere {new_filename}")
        
        # Datei speichern
        out_path = os.path.join(target_dir, new_filename)
        save_cnc_file(converted, out_path)
        
        # Konvertierung prüfen (verbleibende Quellbefehle)
        check_conversion(converted, rules)
        
        # Progress-Update: Fertig
        if progress_callback:
            progress_callback(1, 1, file_path, f"{original_filename} → {new_filename}")
        
        log_conversion_success(original_filename, new_filename, applied_rules)
        logger.info(f"✅ Konvertiert: {original_filename} -> {new_filename}")
        
        return out_path
        
    except Exception as e:
        error_msg = str(e)
        log_conversion_error(os.path.basename(file_path), error_msg)
        logger.error(f"❌ Fehler bei {os.path.basename(file_path)}: {error_msg}")
        
        # Progress-Update: Fehler
        if progress_callback:
            progress_callback(1, 1, file_path, f"Fehler: {error_msg}")
        
        raise


def batch_convert(source_dir: str, target_dir: str, rules: dict,
                  source_prefix_count: int = 0,
                  source_prefix_specific: bool = False,
                  source_prefix_string: str = "",
                  target_prefix_count: int = 0,
                  target_prefix_specific: bool = False,
                  target_prefix_string: str = "",
                  file_endings: list = None,
                  progress_callback: Optional[Callable] = None,
                  cancel_check: Optional[Callable] = None) -> Dict[str, int]:
    """
    Konvertiert alle Dateien im Quellordner (nur im aktuellen Ordner, NICHT in Unterordnern) 
    und speichert sie im Zielordner.
    
    Args:
        source_dir: Quellverzeichnis
        target_dir: Zielverzeichnis
        rules: Konvertierungsregeln aus Excel
        source_prefix_count: Anzahl Zeichen vom Anfang entfernen
        source_prefix_specific: Nur spezifischen String entfernen
        source_prefix_string: Spezifischer Quell-Praefix
        target_prefix_count: Anzahl Zeichen fuer neuen Praefix
        target_prefix_specific: Nur bei spezifischem Quell-Praefix
        target_prefix_string: Neuer Ziel-Praefix
        file_endings: Dateiendungs-Mappings
        progress_callback: Callback für Progress-Updates (current, total, filename, status)
        cancel_check: Callback zum Prüfen ob abgebrochen werden soll
        
    Returns:
        Dictionary mit Statistiken: {'success': int, 'failed': int, 'total': int}
        
    Raises:
        Exception: Bei kritischen Fehlern (Verzeichnis nicht gefunden, etc.)
    """
    logger = get_logger()
    
    if file_endings is None:
        file_endings = []
    
    # Validierung
    if not os.path.exists(source_dir):
        raise FileNotFoundError(f"Quellordner nicht gefunden: {source_dir}")
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)

    # Nur Dateien im aktuellen Ordner, KEINE Unterordner (flache Struktur)
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
        logger.warning("⚠ Keine Dateien im Quellordner gefunden.")
        return {'success': 0, 'failed': 0, 'total': 0}

    total_files = len(files)
    log_conversion_start(source_dir, target_dir, batch_mode=True)
    logger.info(f"🔄 Starte Batch-Konvertierung: {total_files} Dateien aus '{source_dir}' -> '{target_dir}'")
    logger.info(f"📁 Nur Dateien im aktuellen Ordner werden konvertiert (keine Unterordner).")

    success, failed = 0, 0
    
    for i, filename in enumerate(files, 1):
        # Abbruch-Check vor jeder Datei
        if cancel_check and cancel_check():
            logger.info("🛑 Batch-Konvertierung abgebrochen vom Benutzer.")
            break
            
        file_path = os.path.join(source_dir, filename)
        
        # Progress-Update: Aktuelle Datei
        if progress_callback:
            progress_callback(i-1, total_files, file_path, f"Bearbeite {filename} ({i}/{total_files})")
        
        try:
            # Einzeldatei konvertieren
            convert_single_file(
                file_path, target_dir, rules,
                source_prefix_count=source_prefix_count,
                source_prefix_specific=source_prefix_specific,
                source_prefix_string=source_prefix_string,
                target_prefix_count=target_prefix_count,
                target_prefix_specific=target_prefix_specific,
                target_prefix_string=target_prefix_string,
                file_endings=file_endings,
                cancel_check=cancel_check  # Cancel-Check an Einzelkonvertierung weiterreichen
            )
            success += 1
            
            # Progress-Update: Erfolg
            if progress_callback:
                progress_callback(i, total_files, file_path, f"✅ {filename} erfolgreich")
                
        except Exception as e:
            failed += 1
            error_msg = str(e)
            
            # Progress-Update: Fehler
            if progress_callback:
                progress_callback(i, total_files, file_path, f"❌ Fehler: {error_msg}")
            
            # Einzelfehler nicht weiterwerfen, damit Batch weiterlaufen kann
            logger.error(f"❌ Fehler bei {filename}: {error_msg}")
    
    # Abschließende Statistiken
    stats = {'success': success, 'failed': failed, 'total': total_files}
    log_batch_summary(total_files, success, failed)
    logger.info(f"\n📊 Batch-Ergebnis: {success} erfolgreich, {failed} fehlgeschlagen von {total_files} Dateien.")
    
    return stats


def count_applied_rules(original_lines: List[str], converted_lines: List[str], rules: Dict[str, str]) -> int:
    """
    Zählt die Anzahl der angewendeten Regeln (grobe Schätzung).
    
    Args:
        original_lines: Ursprüngliche Zeilen
        converted_lines: Konvertierte Zeilen
        rules: Angewendete Regeln
        
    Returns:
        Anzahl der wahrscheinlich angewendeten Regeln
    """
    if not rules:
        return 0
        
    # Einfache Heuristik: Zähle wie viele Quellstrings im Original vorkommen (für Logging)
    original_text = " ".join(original_lines).upper()
    applied_count = 0
    
    for source_pattern in rules.keys():
        if source_pattern.upper() in original_text:
            applied_count += 1
    
    return applied_count


