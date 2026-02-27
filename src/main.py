import sys

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from app import ApiTestApp
from config.di_container import get_container


def create_light_palette() -> QPalette:
    """Return a simple optional light palette."""
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(245, 245, 245))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    return palette


def main() -> int:
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setPalette(create_light_palette())

    container = get_container()
    win = ApiTestApp(container=container)
    win.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
