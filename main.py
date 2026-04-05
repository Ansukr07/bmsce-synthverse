import sys


def _preload_torch_before_qt():
    """Work around Windows DLL init failures when torch is imported after Qt startup."""
    try:
        import torch  # noqa: F401
    except Exception as e:
        # Keep GUI booting; inference session will report detailed runtime errors if needed.
        print(f"[WARN] Torch preload failed: {e}")


_preload_torch_before_qt()

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
import qdarktheme
from trafficlab.gui.main_window import MainWindow


def _apply_dark_theme(app: QApplication):
    """Support both modern and legacy qdarktheme APIs."""
    if hasattr(qdarktheme, "setup_theme"):
        qdarktheme.setup_theme("dark")
        return
    if hasattr(qdarktheme, "load_stylesheet"):
        app.setStyleSheet(qdarktheme.load_stylesheet())
        return
    print("[WARN] qdarktheme theme API not available; using default Qt theme.")


def main():
    app = QApplication(sys.argv)

    app.setWindowIcon(QIcon("./media/icon.png"))

    _apply_dark_theme(app)

    win = MainWindow()
    win.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
