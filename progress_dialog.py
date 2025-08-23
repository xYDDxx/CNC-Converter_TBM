from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
import os
import time
from typing import Callable, Optional

class ConversionWorker(QThread):
    """Worker-Thread für die Konvertierung."""
    progress_updated = pyqtSignal(int, str, str)  # progress, current_file, status
    conversion_finished = pyqtSignal(bool, str, dict)  # success, message, stats
    error_occurred = pyqtSignal(str, str)  # file, error_msg
    
    def __init__(self, conversion_func: Callable, *args, **kwargs):
        super().__init__()
        self.conversion_func = conversion_func
        self.args = args
        self.kwargs = kwargs
        self.cancelled = False
        
    def run(self):
        """Führt die Konvertierung im separaten Thread aus."""
        try:
            # Callback-Funktionen für Progress-Updates einrichten
            self.kwargs['progress_callback'] = self.update_progress
            self.kwargs['cancel_check'] = lambda: self.cancelled
            
            # Konvertierung ausführen
            result = self.conversion_func(*self.args, **self.kwargs)
            
            if not self.cancelled:
                if isinstance(result, dict):
                    # Batch-Konvertierung
                    success = result.get('success', 0) > 0
                    message = f"Konvertierung abgeschlossen: {result.get('success', 0)} erfolgreich, {result.get('failed', 0)} fehlgeschlagen"
                    self.conversion_finished.emit(success, message, result)
                else:
                    # Einzeldatei-Konvertierung
                    self.conversion_finished.emit(True, "Datei erfolgreich konvertiert", {'success': 1, 'failed': 0})
                    
        except Exception as e:
            if not self.cancelled:
                self.conversion_finished.emit(False, f"Unerwarteter Fehler: {str(e)}", {'success': 0, 'failed': 1})
    
    def update_progress(self, current: int, total: int, current_file: str = "", status: str = ""):
        """Callback für Progress-Updates."""
        if not self.cancelled:
            progress = int((current / max(total, 1)) * 100)
            self.progress_updated.emit(progress, current_file, status)
    
    def cancel(self):
        """Bricht die Konvertierung ab."""
        self.cancelled = True


class ProgressDialog(QDialog):
    """Dialog für Fortschrittsanzeige mit Abbruch-Möglichkeit."""
    
    def __init__(self, parent=None, title="Konvertierung läuft..."):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(500, 300)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint)
        
        self.worker = None
        self.start_time = time.time()
        self.setup_ui()
        
        # Timer für Zeitmessung
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Jede Sekunde
        
    def setup_ui(self):
        """Erstellt die UI-Elemente."""
        layout = QVBoxLayout()
        
        # Titel
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(10)
        
        self.title_label = QLabel("Konvertierung wird vorbereitet...")
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Fortschrittsbalken
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Status-Informationen
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        info_layout = QVBoxLayout()
        
        self.current_file_label = QLabel("Aktuelle Datei: -")
        self.status_label = QLabel("Status: Bereit")
        self.time_label = QLabel("Verstrichene Zeit: 00:00")
        self.stats_label = QLabel("Fortschritt: 0 / 0")
        
        info_layout.addWidget(self.current_file_label)
        info_layout.addWidget(self.status_label)
        info_layout.addWidget(self.time_label)
        info_layout.addWidget(self.stats_label)
        info_frame.setLayout(info_layout)
        layout.addWidget(info_frame)
        
        # Log-Ausgabe (scrollbar)
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(80)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton("Abbrechen")
        self.cancel_btn.clicked.connect(self.cancel_conversion)
        
        self.close_btn = QPushButton("Schließen")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setEnabled(False)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def start_conversion(self, conversion_func: Callable, *args, **kwargs):
        """Startet die Konvertierung im Worker-Thread."""
        self.worker = ConversionWorker(conversion_func, *args, **kwargs)
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.conversion_finished.connect(self.on_conversion_finished)
        self.worker.error_occurred.connect(self.on_error_occurred)
        
        self.add_log("Konvertierung gestartet...")
        self.worker.start()
    
    def on_progress_updated(self, progress: int, current_file: str, status: str):
        """Aktualisiert die Progress-Anzeige."""
        self.progress_bar.setValue(progress)
        
        if current_file:
            filename = os.path.basename(current_file)
            self.current_file_label.setText(f"Aktuelle Datei: {filename}")
        
        if status:
            self.status_label.setText(f"Status: {status}")
            if "→" in status:  # Erfolgreiche Konvertierung
                self.add_log(f"✅ {status}")
            elif "Fehler" in status:
                self.add_log(f"❌ {status}")
    
    def on_conversion_finished(self, success: bool, message: str, stats: dict):
        """Wird aufgerufen wenn die Konvertierung abgeschlossen ist."""
        self.timer.stop()
        
        if success:
            self.title_label.setText("✅ Konvertierung erfolgreich abgeschlossen")
            self.progress_bar.setValue(100)
        else:
            self.title_label.setText("❌ Konvertierung fehlgeschlagen")
        
        self.status_label.setText(f"Status: {message}")
        
        # Statistiken anzeigen
        success_count = stats.get('success', 0)
        failed_count = stats.get('failed', 0)
        total = success_count + failed_count
        self.stats_label.setText(f"Ergebnis: {success_count} erfolgreich, {failed_count} fehlgeschlagen von {total}")
        
        # Log-Eintrag
        self.add_log(f"=== {message} ===")
        
        # Buttons umschalten
        self.cancel_btn.setEnabled(False)
        self.close_btn.setEnabled(True)
        
        # Auto-Close nach 3 Sekunden bei erfolgreichem Batch (optional)
        if success and stats.get('success', 0) > 1:
            QTimer.singleShot(3000, self.accept)
    
    def on_error_occurred(self, filename: str, error_msg: str):
        """Wird bei Einzeldatei-Fehlern aufgerufen."""
        self.add_log(f"❌ Fehler bei {os.path.basename(filename)}: {error_msg}")
    
    def cancel_conversion(self):
        """Bricht die laufende Konvertierung ab."""
        if self.worker and self.worker.isRunning():
            self.add_log("Abbruch angefordert...")
            self.title_label.setText("Konvertierung wird abgebrochen...")
            self.worker.cancel()
            self.worker.wait(3000)  # Max 3 Sekunden warten
            
            if self.worker.isRunning():
                self.worker.terminate()
                self.add_log("Konvertierung zwangsweise beendet.")
            else:
                self.add_log("Konvertierung erfolgreich abgebrochen.")
            
            self.title_label.setText("❌ Konvertierung abgebrochen")
            self.cancel_btn.setEnabled(False)
            self.close_btn.setEnabled(True)
    
    def update_time(self):
        """Aktualisiert die Zeitanzeige."""
        elapsed = int(time.time() - self.start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60
        self.time_label.setText(f"Verstrichene Zeit: {minutes:02d}:{seconds:02d}")
    
    def add_log(self, message: str):
        """Fügt eine Nachricht zum Log hinzu."""
        self.log_text.append(message)
        # Automatisch zum Ende scrollen
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        """Behandelt das Schließen des Dialogs."""
        if self.worker and self.worker.isRunning():
            self.cancel_conversion()
        event.accept()