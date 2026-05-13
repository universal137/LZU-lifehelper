from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from desktop.models import AppModel
from desktop.views import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("兰大生活助手")
    model = AppModel()
    window = MainWindow(model)
    window.apply_theme()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

