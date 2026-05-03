from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication
from desktop.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("兰大生活助手")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
