import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CNC-Konverter")
        self.setGeometry(200, 200, 800, 600)

        label = QLabel("Willkommen zum CNC-Konverter", self)
        label.move(20, 20)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
