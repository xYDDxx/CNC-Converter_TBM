import logging
import os
from datetime import datetime

def setup_logger():
    """
    Richtet das Logging-System ein.
    Erstellt Log-Dateien im 'logs' Verzeichnis mit Datum.
    """
    # Logs-Verzeichnis erstellen
    logs_dir = "./logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    # Log-Datei mit Datum
    log_filename = f"cnc_converter_{datetime.now().strftime('%Y%m%d')}.log"
    log_path = os.path.join(logs_dir, log_filename)
    
    # Logger konfigurieren
    logger = logging.getLogger("cnc_converter")
    logger.setLevel(logging.DEBUG)
    
    # Verhindere doppelte Handler
    if not logger.handlers:
        # File Handler
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Console Handler für wichtige Meldungen
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

def get_logger():
    """Gibt den konfigurierten Logger zurück."""
    return logging.getLogger("cnc_converter")

def log_conversion_start(source_path: str, target_path: str, batch_mode: bool = False):
    """Protokolliert den Start einer Konvertierung."""
    logger = get_logger()
    mode = "Batch" if batch_mode else "Einzeldatei"
    logger.info(f"=== Konvertierung gestartet ({mode}) ===")
    logger.info(f"Quelle: {source_path}")
    logger.info(f"Ziel: {target_path}")

def log_conversion_success(source_file: str, target_file: str, rules_applied: int = 0):
    """Protokolliert erfolgreiche Konvertierung."""
    logger = get_logger()
    logger.info(f"✅ Erfolgreich: {source_file} → {target_file} ({rules_applied} Regeln angewendet)")

def log_conversion_error(source_file: str, error: str):
    """Protokolliert Konvertierungsfehler."""
    logger = get_logger()
    logger.error(f"❌ Fehler bei {source_file}: {error}")

def log_validation_error(errors: list):
    """Protokolliert Validierungsfehler."""
    logger = get_logger()
    logger.warning("⚠️ Validierungsfehler:")
    for error in errors:
        logger.warning(f"  - {error}")

def log_batch_summary(total: int, success: int, failed: int):
    """Protokolliert Batch-Zusammenfassung."""
    logger = get_logger()
    logger.info(f"=== Batch-Konvertierung abgeschlossen ===")
    logger.info(f"Gesamt: {total}, Erfolgreich: {success}, Fehlgeschlagen: {failed}")

def log_config_change(key: str, old_value, new_value):
    """Protokolliert Konfigurationsänderungen."""
    logger = get_logger()
    logger.debug(f"Config geändert: {key} = '{old_value}' → '{new_value}'")