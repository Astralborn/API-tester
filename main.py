import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from app import VapixApp

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Optional light palette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(245,245,245))
    palette.setColor(QPalette.Base, QColor(255,255,255))
    app.setPalette(palette)

    win = VapixApp()
    win.show()
    sys.exit(app.exec())
