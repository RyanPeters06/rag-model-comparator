import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Pre-load fastembed/onnxruntime BEFORE Qt so their DLLs don't conflict on Windows
try:
    from fastembed import TextEmbedding as _  # noqa: F401
    del _
except Exception:
    pass  # Missing or broken — will surface as a clear error when indexing

from PyQt5.QtWidgets import QApplication, QMessageBox

from app.gui.main_window import MainWindow
from app.gui.theme import DARK_STYLESHEET


def _global_exception_hook(exc_type, exc_value, exc_traceback):
    """Show unexpected top-level exceptions in a dialog instead of crashing."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    detail = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    app = QApplication.instance()
    if app:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Unexpected Error")
        msg.setText(
            f"An unexpected error occurred: {exc_type.__name__}: {exc_value}\n\n"
            "The application will try to continue. Click 'Show Details' for the full traceback."
        )
        msg.setDetailedText(detail)
        msg.exec_()
    else:
        sys.__excepthook__(exc_type, exc_value, exc_traceback)


sys.excepthook = _global_exception_hook


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Plant AI Comparison")
    app.setStyleSheet(DARK_STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
