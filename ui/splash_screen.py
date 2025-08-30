import os
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPixmap, QPainter, QPen, QFont, QFontMetrics
from PyQt6.QtCore import Qt


class SplashScreen(QWidget):
    """Splash Screen für den CNC-Konverter."""
    
    def __init__(self):
        super().__init__()
        
        # Vollbildmodus setzen
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        
        # Fenster-Eigenschaften
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        
        # Hintergrundfarbe auf Reinweiß setzen
        self.setStyleSheet("background-color: rgba(255,255,255,255);")
        
        # Logo-Pfad
        self.logo_path = os.path.join("img", "tbm_peening_controls_logo_Aufkleber.png")
        
        # Entwickler-Text
        self.developer_text = "Developed by Ian Felder"
    
    def paintEvent(self, event):
        """Überschreibt die Zeichenfunktion um Logo und Text zu zeichnen."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Logo laden und zentrieren
        logo_pixmap = QPixmap(self.logo_path)
        if not logo_pixmap.isNull():
            # Logo auf 400x200 skalieren
            scaled_logo = logo_pixmap.scaled(
                400, 200,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Logo in der Mitte zeichnen
            x = (self.width() - scaled_logo.width()) // 2
            y = (self.height() - scaled_logo.height()) // 2 - 50  # Etwas nach oben verschieben
            painter.drawPixmap(x, y, scaled_logo)
        
        # Entwickler-Text unten rechts zeichnen
        painter.setPen(QPen(Qt.GlobalColor.black))
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        
        # Text-Maße berechnen
        text_rect = painter.fontMetrics().boundingRect(self.developer_text)
        text_x = self.width() - text_rect.width() - 20
        text_y = self.height() - 20
        
        painter.drawText(text_x, text_y, self.developer_text)
