import sys

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from app import VapixApp


def create_light_palette() -> QPalette:
    """Return a simple optional light palette."""
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(245, 245, 245))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    return palette


def main() -> int:
    """Application entry point."""
    app = QApplication(sys.argv)

    # Optional light palette
    app.setPalette(create_light_palette())

    win = VapixApp()
    win.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())