from __future__ import annotations

import logging
import sys
import traceback

from PySide6.QtWidgets import QApplication, QMessageBox

from desktop.models import AppModel
from desktop.views import MainWindow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("lzu_lifehelper")


def main() -> None:
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("兰大生活助手")
        model = AppModel()
        window = MainWindow(model)
        window.apply_theme()
        window.show()
        sys.exit(app.exec())
    except Exception:
        logger.critical("未捕获异常", exc_info=True)
        tb = traceback.format_exc()
        try:
            QMessageBox.critical(None, "兰大生活助手 - 运行错误", f"程序遇到严重错误即将退出：\n\n{tb[-500:]}")
        except Exception:
            print(tb, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

