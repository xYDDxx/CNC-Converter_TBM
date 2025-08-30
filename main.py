import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# UI-Module importieren
from ui.splash_screen import SplashScreen
from ui.main_window import CNCConverterUI


def main():
    """Hauptfunktion zum Starten der Anwendung."""
    app = QApplication(sys.argv)
    
    # Splash Screen anzeigen
    splash = SplashScreen()
    splash.show()
    
    # App verarbeiten
    app.processEvents()
    
    # Hauptfenster erstellen
    window = CNCConverterUI()
    
    # Splash Screen nach 2 Sekunden ausblenden und Hauptfenster anzeigen
    QTimer.singleShot(2000, lambda: (splash.close(), window.show()))
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
