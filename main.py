import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from PyQt5.QtWidgets import QApplication

from app.gui.main_window import MainWindow
from app.gui.theme import DARK_STYLESHEET


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Plant AI Comparison")
    app.setStyleSheet(DARK_STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
