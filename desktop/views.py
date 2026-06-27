from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from desktop.models import APP_ROOT, RESOURCE_ROOT, AppModel


ROLE_LABELS = {
    "student": "学生",
    "teacher": "老师",
    "admin": "管理员",
}

STATUS_LABELS = {
    "active": "● 正常",
    "banned": "● 已封禁",
    "normal": "● 正常",
    "removed": "● 已下架",
    "cancelled": "● 已取消",
    "admin_cancelled": "● 强制取消",
}


def set_primary(button: QPushButton) -> QPushButton:
    button.setObjectName("primaryBtn")
    return button


def set_danger(button: QPushButton) -> QPushButton:
    button.setObjectName("dangerBtn")
    return button


def set_secondary(button: QPushButton) -> QPushButton:
    button.setObjectName("secondaryBtn")
    return button


def animate_number_count(label: QLabel, target: int, duration: int = 500) -> None:
    from PySide6.QtCore import QVariantAnimation
    anim = QVariantAnimation()
    anim.setDuration(duration)
    anim.setStartValue(0)
    anim.setEndValue(target)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    anim.valueChanged.connect(lambda v: label.setText(str(int(v))))
    anim.start()
    label._num_anim = anim
    # 颜色闪烁动画：数字变化时短暂变金色再恢复
    flash = QTimer()
    flash.setSingleShot(True)
    label.setStyleSheet("color: #FFD700;")
    flash.timeout.connect(lambda: label.setStyleSheet(""))
    flash.start(duration + 200)
    label._flash_timer = flash


def animate_dialog_open(dialog: QDialog) -> None:
    effect = QGraphicsOpacityEffect(dialog)
    dialog.setGraphicsEffect(effect)
    anim_opacity = QPropertyAnimation(effect, b"opacity")
    anim_opacity.setDuration(250)
    anim_opacity.setStartValue(0.0)
    anim_opacity.setEndValue(1.0)
    anim_opacity.setEasingCurve(QEasingCurve.OutCubic)
    anim_geometry = QPropertyAnimation(dialog, b"geometry")
    anim_geometry.setDuration(250)
    anim_geometry.setEasingCurve(QEasingCurve.OutCubic)
    parent = dialog.parentWidget()
    if parent:
        center = parent.rect().center()
        w, h = dialog.width(), dialog.height()
        small = QRectF(center.x() - w // 4, center.y() - h // 4, w // 2, h // 2).toRect()
        full = QRectF(center.x() - w // 2, center.y() - h // 2, w, h).toRect()
        anim_geometry.setStartValue(small)
        anim_geometry.setEndValue(full)
    anim_opacity.start()
    anim_geometry.start()
    dialog._open_opacity = anim_opacity
    dialog._open_geometry = anim_geometry


def card_frame() -> QFrame:
    frame = QFrame()
    frame.setObjectName("cardFrame")
    return frame


def status_badge(text: str, status: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("statusBadge")
    if status in {"active", "normal"}:
        label.setProperty("tone", "success")
    elif status in {"banned", "removed", "admin_cancelled", "cancelled"}:
        label.setProperty("tone", "danger" if status in {"banned", "removed"} else "muted")
    else:
        label.setProperty("tone", "muted")
    return label


ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "images"

CATEGORY_IMAGES = {
    "书籍": "cat_books.jpg",
    "运动": "cat_sports.jpg",
    "数码": "cat_electronics.jpg",
    "日用": "cat_daily.jpg",
    "资料": "cat_clothing.jpg",
    "器材": "cat_transport.jpg",
}

ACTIVITY_CATEGORY_IMAGES = {
    "公益": "act_公益.jpg",
    "体育": "act_体育.jpg",
    "学术": "act_学术.jpg",
    "文艺": "act_文艺.jpg",
    "成长": "act_成长.jpg",
}

MOMENT_CATEGORY_IMAGES = {
    "校园通知": "moment_通知.jpg",
    "失物招领": "moment_失物.jpg",
    "吐槽问答": "moment_问答.jpg",
}


def product_pixmap(image_path: str | None, width: int, height: int, category: str = "", title: str = "") -> QPixmap:
    if image_path:
        target = APP_ROOT / image_path
        if target.exists():
            pixmap = QPixmap(str(target))
            if not pixmap.isNull():
                return pixmap.scaled(width, height, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    # 根据标题关键词匹配具体商品图片
    title_keywords = {
        "平板": "prod_tablet.jpg", "支架": "prod_tablet.jpg",
        "键盘": "prod_keyboard.jpg", "机械": "prod_keyboard.jpg",
        "台灯": "prod_desklamp.jpg", "灯": "prod_light.jpg",
        "笔记": "prod_notebook.jpg", "课程": "prod_notebook.jpg",
        "教材": "prod_book.jpg", "数学": "prod_book.jpg", "单词": "prod_book.jpg",
        "羽毛球": "prod_shuttle.jpg", "球": "prod_shuttle.jpg",
        "摄影": "prod_light.jpg", "灯光": "prod_light.jpg",
    }
    # 也按分类做兜底匹配
    cat_keywords = {
        "数码": ["prod_keyboard.jpg", "prod_tablet.jpg"],
        "日用": ["prod_desklamp.jpg"],
        "资料": ["prod_notebook.jpg"],
        "书籍": ["prod_book.jpg"],
        "运动": ["prod_shuttle.jpg"],
        "器材": ["prod_light.jpg"],
    }
    # 先按标题匹配
    chosen = ""
    for kw, fname in title_keywords.items():
        if kw in title:
            chosen = fname
            break
    # 标题没匹配到，按分类兜底
    if not chosen and category in cat_keywords:
        chosen = cat_keywords[category][0]
    if chosen:
        img_path = ASSETS_DIR / chosen
        if img_path.exists():
            pix = QPixmap(str(img_path))
            if not pix.isNull():
                return pix.scaled(width, height, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    # 兜底
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor("#E8ECF1"))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QColor("#6B7280"))
    painter.setFont(QFont("Microsoft YaHei", 14))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, category or "商品")
    painter.end()
    return pixmap


class Toast(QFrame):
    _active_toasts: list = []

    def __init__(self, parent: QWidget, message: str, success: bool = True) -> None:
        super().__init__(parent)
        self.setObjectName("toast")
        self.setFixedWidth(320)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        icon = QLabel("✓" if success else "!")
        icon.setObjectName("toastIcon")
        icon.setProperty("tone", "success" if success else "danger")
        text = QLabel(message)
        text.setObjectName("toastText")
        text.setWordWrap(True)
        layout.addWidget(icon)
        layout.addWidget(text, 1)
        self.adjustSize()
        target_x = parent.width() - self.width() - 24
        idx = len(Toast._active_toasts)
        target_y = 24 + idx * (self.height() + 10)
        start_x = parent.width() + 20
        self.move(start_x, target_y)
        Toast._active_toasts.append(self)
        anim_in = QPropertyAnimation(self, b"pos")
        anim_in.setDuration(300)
        anim_in.setStartValue(self.pos())
        anim_in.setEndValue(QRectF(target_x, target_y, 0, 0).toRect())
        anim_in.setEasingCurve(QEasingCurve.OutCubic)
        opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(opacity)
        fade_in = QPropertyAnimation(opacity, b"opacity")
        fade_in.setDuration(300)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        anim_in.start()
        fade_in.start()
        self._anim_in = anim_in
        self._fade_in = fade_in
        QTimer.singleShot(2200, self._fade_out)

    def _fade_out(self) -> None:
        opacity = self.graphicsEffect()
        if isinstance(opacity, QGraphicsOpacityEffect):
            fade_out = QPropertyAnimation(opacity, b"opacity")
            fade_out.setDuration(300)
            fade_out.setStartValue(1.0)
            fade_out.setEndValue(0.0)
            fade_out.setEasingCurve(QEasingCurve.InCubic)
            fade_out.start()
            self._fade_out_anim = fade_out
        slide_out = QPropertyAnimation(self, b"pos")
        slide_out.setDuration(300)
        slide_out.setStartValue(self.pos())
        slide_out.setEndValue(QRectF(self.pos().x(), self.pos().y() - 40, 0, 0).toRect())
        slide_out.setEasingCurve(QEasingCurve.InCubic)
        slide_out.start()
        self._slide_out = slide_out
        if self in Toast._active_toasts:
            Toast._active_toasts.remove(self)
            self._reposition_remaining()
        QTimer.singleShot(350, self.deleteLater)

    def _reposition_remaining(self) -> None:
        parent = self.parentWidget()
        if not parent:
            return
        for i, toast in enumerate(Toast._active_toasts):
            target_y = 24 + i * (toast.height() + 10)
            anim = QPropertyAnimation(toast, b"pos")
            anim.setDuration(200)
            anim.setStartValue(toast.pos())
            anim.setEndValue(QRectF(parent.width() - toast.width() - 24, target_y, 0, 0).toRect())
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.start()
            toast._reposition_anim = anim


class AnimatedStackedWidget(QStackedWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._animating = False

    def animated_switch(self, index: int) -> None:
        if self._animating or index == self.currentIndex():
            return
        if index < 0 or index >= self.count():
            return
        old_widget = self.currentWidget()
        self._animating = True
        new_widget = self.widget(index)
        opacity_effect = QGraphicsOpacityEffect(new_widget)
        new_widget.setGraphicsEffect(opacity_effect)
        new_widget.show()
        fade_in = QPropertyAnimation(opacity_effect, b"opacity")
        fade_in.setDuration(200)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.OutCubic)
        fade_in.start()
        self._fade_in = fade_in
        self.setCurrentIndex(index)
        fade_in.finished.connect(self._on_animation_done)

    def _on_animation_done(self) -> None:
        self._animating = False
        widget = self.currentWidget()
        if widget:
            widget.setGraphicsEffect(None)


class BarChart(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict] = []
        self.setMinimumHeight(230)

    def set_data(self, rows: list[dict]) -> None:
        self.rows = rows
        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        from PySide6.QtGui import QLinearGradient, QPen
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(40, 22, -22, -34)
        # 底部轴线
        painter.setPen(QColor("#DEE2E6"))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        if not self.rows:
            painter.setPen(QColor("#6C757D"))
            painter.drawText(rect, Qt.AlignCenter, "暂无统计数据")
            painter.end()
            return
        max_value = max([row["total"] for row in self.rows] + [1])
        # 水平参考线（虚线）
        grid_pen = QPen(QColor("#E8ECF1"), 1, Qt.DashLine)
        painter.setPen(grid_pen)
        for i in range(1, 5):
            gy = rect.bottom() - int(rect.height() * i / 4)
            painter.drawLine(int(rect.left()), gy, int(rect.right()), gy)
            # Y轴刻度标签
            painter.setPen(QColor("#9CA3AF"))
            painter.setFont(QFont("Microsoft YaHei", 8))
            painter.drawText(QRectF(0, gy - 10, 36, 20), Qt.AlignRight | Qt.AlignVCenter, str(int(max_value * i / 4)))
            painter.setPen(grid_pen)
        gap = 16
        bar_width = max(34, int((rect.width() - gap * (len(self.rows) - 1)) / len(self.rows)))
        for index, row in enumerate(self.rows):
            value = row["total"]
            height = int(rect.height() * (value / max_value)) if max_value else 0
            x = rect.left() + index * (bar_width + gap)
            y = rect.bottom() - height
            bar_rect = QRectF(x, y, bar_width, height)
            # 渐变色：低值蓝色 → 高值金色
            ratio = value / max_value if max_value else 0
            grad = QLinearGradient(x, y, x, rect.bottom())
            r_start = int(0 + 201 * ratio)
            g_start = int(169 + 0 * ratio)
            b_start = int(150 - 88 * ratio)
            r_end = int(0 + 184 * ratio)
            g_end = int(169 - 21 * ratio)
            b_end = int(150 - 103 * ratio)
            grad.setColorAt(0, QColor(r_start, g_start, b_start))
            grad.setColorAt(1, QColor(r_end, g_end, b_end))
            painter.setBrush(grad)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(bar_rect, 5, 5)
            # 数值标签
            painter.setPen(QColor("#212529"))
            painter.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
            painter.drawText(QRectF(x, y - 26, bar_width, 20), Qt.AlignCenter, str(value))
            # 名称标签（省略号截断）
            painter.setPen(QColor("#6C757D"))
            painter.setFont(QFont("Microsoft YaHei", 8))
            metrics = painter.fontMetrics()
            name = row["name"]
            elided = metrics.elidedText(name, Qt.ElideRight, bar_width + 20)
            painter.drawText(QRectF(x - 10, rect.bottom() + 6, bar_width + 20, 24), Qt.AlignCenter, elided)
        painter.end()


class ProductDialog(QDialog):
    def __init__(self, parent: QWidget, model: AppModel) -> None:
        super().__init__(parent)
        self.model = model
        self.image_path: str | None = None
        self.setWindowTitle("发布商品")
        self.resize(480, 460)
        layout = QFormLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(30, 30, 30, 30)
        self.title_input = QLineEdit()
        self.category_input = QComboBox()
        self.category_input.addItems(self.model.product_categories()[1:])
        self.campus_input = QComboBox()
        self.campus_input.addItems(["榆中校区", "城关校区"])
        self.price_input = QLineEdit()
        self.desc_input = QTextEdit()
        self.desc_input.setMinimumHeight(100)
        self.image_label = QLabel("未选择图片")
        pick = set_secondary(QPushButton("选择图片"))
        pick.clicked.connect(self.pick_image)
        submit = set_primary(QPushButton("确认发布"))
        submit.clicked.connect(self.accept)
        layout.addRow("标题", self.title_input)
        layout.addRow("分类", self.category_input)
        layout.addRow("校区", self.campus_input)
        layout.addRow("价格", self.price_input)
        layout.addRow("描述", self.desc_input)
        layout.addRow(self.image_label, pick)
        layout.addRow(submit)

    def pick_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "选择图片", str(APP_ROOT), "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.image_path = file_path
            self.image_label.setText(Path(file_path).name)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        animate_dialog_open(self)


class ActivityDialog(QDialog):
    def __init__(self, parent: QWidget, model: AppModel) -> None:
        super().__init__(parent)
        self.model = model
        self.setWindowTitle("发布活动")
        self.resize(500, 420)
        layout = QFormLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(30, 30, 30, 30)
        self.title_input = QLineEdit()
        self.category_input = QComboBox()
        self.category_input.addItems(self.model.activity_categories()[1:])
        self.location_input = QLineEdit()
        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText("例如 2026-06-20 19:00")
        self.capacity_input = QLineEdit()
        self.summary_input = QTextEdit()
        self.summary_input.setMinimumHeight(100)
        submit = set_primary(QPushButton("发布活动"))
        submit.clicked.connect(self.accept)
        layout.addRow("标题", self.title_input)
        layout.addRow("分类", self.category_input)
        layout.addRow("地点", self.location_input)
        layout.addRow("时间", self.time_input)
        layout.addRow("人数上限", self.capacity_input)
        layout.addRow("简介", self.summary_input)
        layout.addRow(submit)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        animate_dialog_open(self)


class MomentDialog(QDialog):
    def __init__(self, parent: QWidget, model: AppModel) -> None:
        super().__init__(parent)
        self.model = model
        self.image_path: str | None = None
        self.setWindowTitle("发布动态")
        self.resize(480, 360)
        layout = QFormLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(30, 30, 30, 30)
        self.category_input = QComboBox()
        self.category_input.addItems(self.model.moment_categories()[1:])
        self.content_input = QTextEdit()
        self.content_input.setMinimumHeight(120)
        self.image_label = QLabel("未选择图片")
        pick = set_secondary(QPushButton("附加图片"))
        pick.clicked.connect(self.pick_image)
        submit = set_primary(QPushButton("发布动态"))
        submit.clicked.connect(self.accept)
        layout.addRow("分类", self.category_input)
        layout.addRow("内容", self.content_input)
        layout.addRow(self.image_label, pick)
        layout.addRow(submit)

    def pick_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "选择图片", str(APP_ROOT), "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.image_path = file_path
            self.image_label.setText(Path(file_path).name)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        animate_dialog_open(self)


class CommentDialog(QDialog):
    def __init__(self, parent: QWidget, title: str = "发表评论", prompt: str = "填写内容") -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(400, 260)
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(30, 30, 30, 30)
        label = QLabel(prompt)
        label.setObjectName("dialogHint")
        self.content_input = QTextEdit()
        self.content_input.setMinimumHeight(120)
        submit = set_primary(QPushButton("提交"))
        submit.clicked.connect(self.accept)
        layout.addWidget(label)
        layout.addWidget(self.content_input, 1)
        layout.addWidget(submit)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        animate_dialog_open(self)


class ConfirmDialog(QDialog):
    def __init__(self, parent: QWidget, title: str, message: str, danger: bool = False) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(440, 240)
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(30, 30, 30, 30)
        header = QLabel(title)
        header.setObjectName("dialogTitle")
        body = QLabel(message)
        body.setObjectName("dialogBody")
        body.setWordWrap(True)
        buttons = QHBoxLayout()
        buttons.setSpacing(12)
        cancel = set_secondary(QPushButton("返回"))
        ok = set_danger(QPushButton("确认执行")) if danger else set_primary(QPushButton("确认"))
        cancel.clicked.connect(self.reject)
        ok.clicked.connect(self.accept)
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(ok)
        layout.addWidget(header)
        layout.addWidget(body)
        layout.addStretch(1)
        layout.addLayout(buttons)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        animate_dialog_open(self)


class ReasonDialog(QDialog):
    def __init__(self, parent: QWidget, title: str, message: str, placeholder: str = "填写操作原因，便于留痕") -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(520, 350)
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(30, 30, 30, 30)
        header = QLabel(title)
        header.setObjectName("dialogTitle")
        body = QLabel(message)
        body.setObjectName("dialogBody")
        body.setWordWrap(True)
        self.reason_input = QTextEdit()
        self.reason_input.setPlaceholderText(placeholder)
        self.reason_input.setMinimumHeight(120)
        buttons = QHBoxLayout()
        buttons.setSpacing(12)
        cancel = set_secondary(QPushButton("取消"))
        ok = set_danger(QPushButton("确认并记录"))
        cancel.clicked.connect(self.reject)
        ok.clicked.connect(self.accept)
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(ok)
        layout.addWidget(header)
        layout.addWidget(body)
        layout.addWidget(self.reason_input, 1)
        layout.addLayout(buttons)

    def reason(self) -> str:
        return self.reason_input.toPlainText().strip()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        animate_dialog_open(self)


class DetailDialog(QDialog):
    def __init__(self, parent: QWidget, title: str, subtitle: str = "", status_text: str = "", status: str = "normal") -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(720, 560)
        self._setup_open_animation()
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(20, 20, 20, 20)
        self.root.setSpacing(14)
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("dialogTitle")
        title_box.addWidget(title_label)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setObjectName("mutedText")
            title_box.addWidget(sub)
        header.addLayout(title_box, 1)
        if status_text:
            header.addWidget(status_badge(status_text, status))
        self.root.addLayout(header)

    def add_meta_grid(self, items: list[tuple[str, str]]) -> None:
        frame = QFrame()
        frame.setObjectName("detailMeta")
        grid = QGridLayout(frame)
        grid.setContentsMargins(14, 12, 14, 12)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(8)
        for index, (label, value) in enumerate(items):
            k = QLabel(label)
            k.setObjectName("metaLabel")
            v = QLabel(value)
            v.setObjectName("metaValue")
            grid.addWidget(k, index // 2 * 2, index % 2)
            grid.addWidget(v, index // 2 * 2 + 1, index % 2)
        self.root.addWidget(frame)

    def add_section(self, title: str, text: str, min_height: int = 90) -> QTextEdit:
        label = QLabel(title)
        label.setObjectName("sectionTitle")
        box = QTextEdit()
        box.setReadOnly(True)
        box.setMinimumHeight(min_height)
        formatted = text.replace("\n", "<br>")
        box.setHtml(
            f'<div style="color:#1A1A2E; font-size:14px; line-height:1.7; padding:8px;">'
            f'{formatted}</div>'
        )
        self.root.addWidget(label)
        self.root.addWidget(box)
        return box

    def add_actions(self, actions: list[tuple[str, callable, str]]) -> None:
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        for text, handler, tone in actions:
            button = set_danger(QPushButton(text)) if tone == "danger" else set_primary(QPushButton(text)) if tone == "primary" else set_secondary(QPushButton(text))
            button.clicked.connect(handler)
            buttons.addWidget(button)
        self.root.addLayout(buttons)

    def _setup_open_animation(self) -> None:
        pass

    def showEvent(self, event) -> None:
        super().showEvent(event)
        animate_dialog_open(self)


class LoginVisualPanel(QFrame):
    """登录页左侧视觉面板，绘制校园背景图+遮罩"""
    _hero_pix: QPixmap | None = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("loginVisual")
        self.setMinimumWidth(450)
        if LoginVisualPanel._hero_pix is None:
            path = ASSETS_DIR / "login_hero.jpg"
            if path.exists():
                LoginVisualPanel._hero_pix = QPixmap(str(path))

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QColor
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if LoginVisualPanel._hero_pix and not LoginVisualPanel._hero_pix.isNull():
            scaled = LoginVisualPanel._hero_pix.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            p.drawPixmap(x, y, scaled)
            p.fillRect(0, 0, self.width(), self.height(), QColor(26, 26, 46, 130))
        else:
            p.fillRect(0, 0, self.width(), self.height(), QColor("#1A1A2E"))
        p.end()


class AuthPage(QWidget):
    login_success = Signal()
    notify = Signal(str, bool)

    def __init__(self, model: AppModel) -> None:
        super().__init__()
        self.model = model
        self._build_ui()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        visual = LoginVisualPanel()
        visual_layout = QVBoxLayout(visual)
        visual_layout.setContentsMargins(60, 70, 60, 70)
        logo = QLabel("LZU")
        logo.setObjectName("loginLogo")
        title = QLabel("兰大生活助手")
        title.setObjectName("loginHeroTitle")
        subtitle = QLabel("二手市场、场馆预约、校园出行、活动报名与生活圈的一站式桌面工作台")
        subtitle.setObjectName("loginHeroSubtitle")
        subtitle.setWordWrap(True)
        visual_layout.addWidget(logo, 0, Qt.AlignLeft)
        visual_layout.addStretch(1)
        visual_layout.addWidget(title)
        visual_layout.addSpacing(8)
        visual_layout.addWidget(subtitle)
        visual_layout.addStretch(2)

        form_wrap = QWidget()
        form_wrap.setObjectName("loginFormWrap")
        form_layout = QVBoxLayout(form_wrap)
        form_layout.setContentsMargins(80, 70, 80, 70)
        form_layout.setSpacing(20)
        title2 = QLabel("登录系统")
        title2.setObjectName("pageTitle")
        desc = QLabel("输入账号密码后，系统会自动根据身份进入用户端或管理端。")
        desc.setObjectName("mutedText")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("账号")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self.submit_login)
        login_btn = set_primary(QPushButton("登录"))
        login_btn.clicked.connect(self.submit_login)
        demo_title = QLabel("演示账号")
        demo_title.setObjectName("sectionTitle")
        demo_row = QHBoxLayout()
        demo_row.setSpacing(10)
        for label, username, password in [
            ("学生", "20230001", "lzu123456"),
            ("老师", "teacher01", "lzu123456"),
            ("管理员", "admin01", "admin123456"),
        ]:
            button = set_secondary(QPushButton(label))
            button.clicked.connect(lambda _checked=False, u=username, p=password: self.fill_demo(u, p))
            demo_row.addWidget(button)
        register_title = QLabel("注册普通账号")
        register_title.setObjectName("sectionTitle")
        self.reg_username = QLineEdit()
        self.reg_username.setPlaceholderText("新账号")
        self.reg_name = QLineEdit()
        self.reg_name.setPlaceholderText("显示姓名")
        self.reg_password = QLineEdit()
        self.reg_password.setPlaceholderText("密码至少 8 位")
        self.reg_password.setEchoMode(QLineEdit.Password)
        self.reg_role = QComboBox()
        self.reg_role.addItems(["student", "teacher"])
        self.reg_college = QLineEdit()
        self.reg_college.setPlaceholderText("学院 / 单位")
        register_btn = set_secondary(QPushButton("完成注册"))
        register_btn.clicked.connect(self.submit_register)

        form_layout.addWidget(title2)
        form_layout.addWidget(desc)
        form_layout.addSpacing(16)
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(login_btn)
        form_layout.addSpacing(20)
        form_layout.addWidget(demo_title)
        form_layout.addLayout(demo_row)
        form_layout.addSpacing(28)
        form_layout.addWidget(register_title)
        form_layout.addWidget(self.reg_username)
        form_layout.addWidget(self.reg_name)
        form_layout.addWidget(self.reg_password)
        form_layout.addWidget(self.reg_role)
        form_layout.addWidget(self.reg_college)
        form_layout.addWidget(register_btn)
        form_layout.addStretch(1)

        root.addWidget(visual, 4)
        root.addWidget(form_wrap, 6)

    def fill_demo(self, username: str, password: str) -> None:
        self.username_input.setText(username)
        self.password_input.setText(password)

    def submit_login(self) -> None:
        ok, message = self.model.authenticate(self.username_input.text().strip(), self.password_input.text())
        self.notify.emit(message, ok)
        if ok:
            self.login_success.emit()

    def submit_register(self) -> None:
        ok, message = self.model.register_user(
            self.reg_username.text().strip(),
            self.reg_name.text().strip(),
            self.reg_password.text(),
            self.reg_role.currentText(),
            self.reg_college.text().strip(),
        )
        self.notify.emit(message, ok)
        if ok:
            self.reg_username.clear()
            self.reg_name.clear()
            self.reg_password.clear()
            self.reg_college.clear()


class MainWindow(QMainWindow):
    def __init__(self, model: AppModel) -> None:
        super().__init__()
        self.model = model
        self.setWindowTitle("兰大生活助手")
        self.resize(1100, 700)
        self.setMinimumSize(1100, 700)
        self.root_stack = AnimatedStackedWidget()
        self.user_nav: QListWidget | None = None
        self.admin_nav: QListWidget | None = None
        self.user_pages: QStackedWidget | None = None
        self.admin_pages: QStackedWidget | None = None
        self.current_product_id: int | None = None
        self.current_booking_id: int | None = None
        self.current_route_id: int | None = None
        self.current_activity_id: int | None = None
        self.current_moment_id: int | None = None
        self.current_admin_ids: dict[str, int | None] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        self.auth_page = AuthPage(self.model)
        self.auth_page.login_success.connect(self.enter_after_login)
        self.auth_page.notify.connect(self.show_toast)
        self.root_stack.addWidget(self.auth_page)
        self.setCentralWidget(self.root_stack)

    def apply_theme(self) -> None:
        qss_path = RESOURCE_ROOT / "desktop" / "style.qss"
        if qss_path.exists():
            self.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    def show_toast(self, message: str, success: bool = True) -> None:
        toast = Toast(self, message, success)
        toast.show()

    def enter_after_login(self) -> None:
        user = self.model.require_user()
        if user.role == "admin":
            self.admin_page = self._build_admin_shell()
            self.root_stack.addWidget(self.admin_page)
            self.root_stack.setCurrentWidget(self.admin_page)
            self.refresh_admin_all()
        else:
            self.user_page = self._build_user_shell()
            self.root_stack.addWidget(self.user_page)
            self.root_stack.setCurrentWidget(self.user_page)
            self.refresh_user_all()

    def logout(self) -> None:
        self.model.logout()
        self.root_stack.setCurrentWidget(self.auth_page)

    def _build_sidebar(self, admin: bool = False) -> QFrame:
        user = self.model.require_user()
        side = QFrame()
        side.setObjectName("adminSidebar" if admin else "userSidebar")
        side.setFixedWidth(240)
        layout = QVBoxLayout(side)
        layout.setContentsMargins(20, 24, 20, 24)
        layout.setSpacing(18)
        brand = QLabel("兰大助手")
        brand.setObjectName("sidebarBrand")
        # 用户头像 + 信息行
        user_row = QHBoxLayout()
        user_row.setSpacing(12)
        avatar = QLabel(user.display_name[0] if user.display_name else "?")
        avatar.setObjectName("sidebarAvatar")
        avatar.setStyleSheet(f"background-color: {user.avatar_color};")
        user_row.addWidget(avatar)
        info = QLabel(f"{user.display_name}\n{ROLE_LABELS.get(user.role, user.role)} · {user.college}")
        info.setObjectName("sidebarUser")
        info.setWordWrap(True)
        user_row.addWidget(info, 1)
        nav = QListWidget()
        nav.setObjectName("navList")
        nav.setSpacing(6)
        if admin:
            for item in ["📊 数据总览", "👥 用户管理", "📦 商品管理", "📅 预约管理", "🎉 活动管理", "💬 生活圈审核", "📋 操作日志"]:
                nav.addItem(QListWidgetItem(item))
            self.admin_nav = nav
        else:
            for item in ["🏠 首页概览", "🛍 二手市场", "🏸 场馆预约", "🚌 校园出行", "🎉 活动中心", "💬 生活圈", "👤 个人中心"]:
                nav.addItem(QListWidgetItem(item))
            self.user_nav = nav
        logout = set_secondary(QPushButton("退出登录"))
        logout.clicked.connect(self.logout)
        layout.addWidget(brand)
        layout.addLayout(user_row)
        layout.addSpacing(10)
        layout.addWidget(nav, 1)
        layout.addSpacing(10)
        layout.addWidget(logout)
        return side

    def _shell_page(self, sidebar: QFrame, stack: QStackedWidget) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(sidebar)
        layout.addWidget(stack, 1)
        return page

    def _content_page(self, title: str, subtitle: str = "") -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        page.setObjectName("contentPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)
        top = QVBoxLayout()
        label = QLabel(title)
        label.setObjectName("pageTitle")
        top.addWidget(label)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setObjectName("mutedText")
            top.addWidget(sub)
        layout.addLayout(top)
        return page, layout

    def _scroll_grid_page(self, title: str, subtitle: str = "") -> tuple[QWidget, QVBoxLayout]:
        page, layout = self._content_page(title, subtitle)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(12)
        scroll.setWidget(body)
        layout.addWidget(scroll, 1)
        return page, body_layout

    def _build_user_shell(self) -> QWidget:
        self.user_pages = AnimatedStackedWidget()
        self.user_pages.addWidget(self._build_user_home())
        self.user_pages.addWidget(self._build_market_page())
        self.user_pages.addWidget(self._build_booking_page())
        self.user_pages.addWidget(self._build_transit_page())
        self.user_pages.addWidget(self._build_activity_page())
        self.user_pages.addWidget(self._build_moment_page())
        self.user_pages.addWidget(self._build_profile_page())
        sidebar = self._build_sidebar(admin=False)
        assert self.user_nav is not None
        self.user_nav.currentRowChanged.connect(self.user_pages.animated_switch)
        self.user_nav.setCurrentRow(0)
        return self._shell_page(sidebar, self.user_pages)

    def _build_user_home(self) -> QWidget:
        page, layout = self._content_page("首页概览", "校园服务集中入口，常用信息一屏查看。")
        cards = QHBoxLayout()
        self.user_kpi_labels: dict[str, QLabel] = {}
        kpi_colors = {"products": "blue", "bookings": "green", "tickets": "orange", "activities": "purple"}
        for key, title in [("products", "🛍 在售商品"), ("bookings", "📋 我的预约"), ("tickets", "🎫 校车票"), ("activities", "🎉 已报名活动")]:
            card = card_frame()
            card.setProperty("kpiColor", kpi_colors.get(key, "blue"))
            c = QVBoxLayout(card)
            t = QLabel(title)
            t.setObjectName("kpiTitle")
            v = QLabel("0")
            v.setObjectName("kpiValue")
            c.addWidget(t)
            c.addWidget(v)
            cards.addWidget(card)
            self.user_kpi_labels[key] = v
        layout.addLayout(cards)
        main = QHBoxLayout()
        self.home_products = QTextEdit()
        self.home_products.setReadOnly(True)
        self.home_activities = QTextEdit()
        self.home_activities.setReadOnly(True)
        main.addWidget(self._text_card("最新二手商品", self.home_products))
        main.addWidget(self._text_card("近期活动", self.home_activities))
        layout.addLayout(main, 1)
        return page

    def _text_card(self, title: str, widget: QWidget) -> QFrame:
        frame = card_frame()
        layout = QVBoxLayout(frame)
        label = QLabel(title)
        label.setObjectName("sectionTitle")
        layout.addWidget(label)
        layout.addWidget(widget, 1)
        return frame

    def _build_market_page(self) -> QWidget:
        page, layout = self._scroll_grid_page("二手市场", "网格卡片展示商品，支持发布、筛选、留言。")
        tools = QHBoxLayout()
        tools.setSpacing(12)
        self.market_keyword = QLineEdit()
        self.market_keyword.setPlaceholderText("搜索商品")
        self.market_keyword.setMinimumWidth(200)
        self.market_category = QComboBox()
        self.market_category.setMinimumWidth(120)
        self.market_category.addItems(self.model.product_categories())
        search = set_secondary(QPushButton("筛选"))
        search.clicked.connect(self.refresh_market)
        publish = set_primary(QPushButton("发布商品"))
        publish.clicked.connect(self.open_product_dialog)
        tools.addWidget(self.market_keyword, 1)
        tools.addWidget(self.market_category)
        tools.addWidget(search)
        tools.addWidget(publish)
        layout.addLayout(tools)
        self.market_grid = QGridLayout()
        self.market_grid.setSpacing(18)
        layout.addLayout(self.market_grid)
        layout.addStretch(1)
        return page

    def _build_booking_page(self) -> QWidget:
        page, layout = self._content_page("场馆预约", "查看未来 7 天场馆时段，支持预约与取消。")
        tools = QHBoxLayout()
        tools.setSpacing(12)
        self.booking_category = QComboBox()
        self.booking_category.setMinimumWidth(120)
        self.booking_category.addItems(self.model.venue_categories())
        refresh = set_secondary(QPushButton("刷新"))
        refresh.clicked.connect(self.refresh_bookings)
        book = set_primary(QPushButton("点击预约"))
        book.clicked.connect(self.create_booking)
        cancel = set_danger(QPushButton("取消我的预约"))
        cancel.clicked.connect(self.cancel_booking)
        tools.addWidget(self.booking_category)
        tools.addWidget(refresh)
        tools.addStretch(1)
        tools.addWidget(book)
        tools.addWidget(cancel)
        layout.addLayout(tools)
        self.slot_table = self._table(["场馆", "类别", "校区", "地点", "日期", "时段", "余量"])
        self.slot_table.itemSelectionChanged.connect(self.capture_slot_selection)
        self.booking_table = self._table(["场馆", "地点", "日期", "时段", "状态"])
        self.booking_table.itemSelectionChanged.connect(self.capture_booking_selection)
        layout.addWidget(QLabel("可预约时段"))
        layout.addWidget(self.slot_table, 2)
        layout.addWidget(QLabel("我的预约"))
        layout.addWidget(self.booking_table, 1)
        return page

    def _build_transit_page(self) -> QWidget:
        page, layout = self._content_page("校园出行", "查看校车班次与余票，一键预订。")
        tools = QHBoxLayout()
        tools.setSpacing(12)
        self.bus_campus = QComboBox()
        self.bus_campus.setMinimumWidth(120)
        self.bus_campus.addItems(["全部", "榆中校区", "城关校区"])
        refresh = set_secondary(QPushButton("刷新"))
        refresh.clicked.connect(self.refresh_buses)
        ticket = set_primary(QPushButton("一键购票"))
        ticket.clicked.connect(self.create_ticket)
        tools.addWidget(self.bus_campus)
        tools.addWidget(refresh)
        tools.addStretch(1)
        tools.addWidget(ticket)
        layout.addLayout(tools)
        self.bus_table = self._table(["线路", "出发", "到达", "乘车点", "发车时间", "余座"])
        self.bus_table.itemSelectionChanged.connect(self.capture_route_selection)
        self.ticket_text = QTextEdit()
        self.ticket_text.setReadOnly(True)
        layout.addWidget(self.bus_table, 2)
        layout.addWidget(self._text_card("我的车票", self.ticket_text), 1)
        return page

    def _build_activity_page(self) -> QWidget:
        page, layout = self._content_page("活动中心", "老师可发布活动，学生可报名，支持名单导出。")
        tools = QHBoxLayout()
        tools.setSpacing(12)
        self.activity_category = QComboBox()
        self.activity_category.setMinimumWidth(120)
        self.activity_category.addItems(self.model.activity_categories())
        refresh = set_secondary(QPushButton("刷新"))
        refresh.clicked.connect(self.refresh_activities)
        join = set_primary(QPushButton("报名活动"))
        join.clicked.connect(self.register_activity)
        publish = set_secondary(QPushButton("发布活动"))
        publish.clicked.connect(self.open_activity_dialog)
        export = set_secondary(QPushButton("导出名单"))
        export.clicked.connect(self.export_activity)
        tools.addWidget(self.activity_category)
        tools.addWidget(refresh)
        tools.addStretch(1)
        tools.addWidget(join)
        tools.addWidget(publish)
        tools.addWidget(export)
        layout.addLayout(tools)
        self.activity_table = self._table(["标题", "分类", "组织者", "时间", "地点", "余位", "状态"])
        self.activity_table.itemSelectionChanged.connect(self.open_activity_detail)
        self.activity_detail = QTextEdit()
        self.activity_detail.setReadOnly(True)
        layout.addWidget(self.activity_table, 2)
        layout.addWidget(self.activity_detail, 1)
        return page

    def _build_moment_page(self) -> QWidget:
        page, layout = self._content_page("生活圈", "校园动态、失物招领、问答和活动信息集中发布。")
        tools = QHBoxLayout()
        tools.setSpacing(12)
        self.moment_category = QComboBox()
        self.moment_category.setMinimumWidth(120)
        self.moment_category.addItems(self.model.moment_categories())
        refresh = set_secondary(QPushButton("刷新"))
        refresh.clicked.connect(self.refresh_moments)
        publish = set_primary(QPushButton("发布动态"))
        publish.clicked.connect(self.open_moment_dialog)
        like = set_secondary(QPushButton("点赞/取消"))
        like.clicked.connect(self.toggle_like)
        comment = set_secondary(QPushButton("评论"))
        comment.clicked.connect(self.open_comment_dialog)
        tools.addWidget(self.moment_category)
        tools.addWidget(refresh)
        tools.addStretch(1)
        tools.addWidget(publish)
        tools.addWidget(like)
        tools.addWidget(comment)
        layout.addLayout(tools)
        split = QHBoxLayout()
        split.setSpacing(16)
        self.moment_list = QListWidget()
        self.moment_list.setObjectName("momentList")
        self.moment_list.setIconSize(QSize(48, 48))
        self.moment_list.currentItemChanged.connect(lambda _cur, _old: self.open_moment_detail())
        self.moment_detail = QTextEdit()
        self.moment_detail.setReadOnly(True)
        split.addWidget(self.moment_list, 2)
        split.addWidget(self.moment_detail, 3)
        layout.addLayout(split, 1)
        return page

    def _build_profile_page(self) -> QWidget:
        page, layout = self._content_page("个人中心", "查看个人资料、预约记录和修改密码。")
        # 用户大头像
        user = self.model.require_user()
        avatar_row = QHBoxLayout()
        avatar_row.setSpacing(20)
        big_avatar = QLabel(user.display_name[0] if user.display_name else "?")
        big_avatar.setObjectName("sidebarAvatar")
        big_avatar.setFixedSize(80, 80)
        big_avatar.setStyleSheet(f"background-color: {user.avatar_color}; border-radius: 40px; color: #FFFFFF; font-size: 32px; font-weight: bold; qproperty-alignment: AlignCenter;")
        avatar_row.addWidget(big_avatar)
        avatar_info = QVBoxLayout()
        avatar_info.setSpacing(4)
        name_label = QLabel(user.display_name)
        name_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #1A1A2E;")
        role_label = QLabel(f"{ROLE_LABELS.get(user.role, user.role)} · {user.college}")
        role_label.setStyleSheet("color: #6B7280; font-size: 14px;")
        avatar_info.addWidget(name_label)
        avatar_info.addWidget(role_label)
        avatar_info.addStretch(1)
        avatar_row.addLayout(avatar_info, 1)
        layout.addLayout(avatar_row)
        split = QHBoxLayout()
        split.setSpacing(20)
        self.profile_text = QTextEdit()
        self.profile_text.setReadOnly(True)
        form = card_frame()
        f = QFormLayout(form)
        f.setSpacing(16)
        self.old_password = QLineEdit()
        self.old_password.setEchoMode(QLineEdit.Password)
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        submit = set_primary(QPushButton("修改密码"))
        submit.clicked.connect(self.change_password)
        f.addRow("原密码", self.old_password)
        f.addRow("新密码", self.new_password)
        f.addRow("确认密码", self.confirm_password)
        f.addRow(submit)
        split.addWidget(self.profile_text, 2)
        split.addWidget(form, 1)
        layout.addLayout(split, 1)
        return page

    def _build_admin_shell(self) -> QWidget:
        self.admin_pages = AnimatedStackedWidget()
        self.admin_pages.addWidget(self._build_admin_overview())
        self.admin_pages.addWidget(self._build_admin_users())
        self.admin_pages.addWidget(self._build_admin_products())
        self.admin_pages.addWidget(self._build_admin_bookings())
        self.admin_pages.addWidget(self._build_admin_activities())
        self.admin_pages.addWidget(self._build_admin_moments())
        self.admin_pages.addWidget(self._build_admin_logs())
        sidebar = self._build_sidebar(admin=True)
        assert self.admin_nav is not None
        self.admin_nav.currentRowChanged.connect(self.admin_pages.animated_switch)
        self.admin_nav.setCurrentRow(0)
        return self._shell_page(sidebar, self.admin_pages)

    def _build_admin_overview(self) -> QWidget:
        page, layout = self._content_page("数据总览", "系统后台核心指标与场馆预约热度。")
        cards = QHBoxLayout()
        self.admin_kpi_labels: dict[str, QLabel] = {}
        admin_kpi_colors = {"users": "teal", "today_bookings": "orange", "products": "blue", "moments": "purple"}
        for key, title in [("users", "👥 用户总数"), ("today_bookings", "📅 今日预约"), ("products", "📦 在售商品"), ("moments", "📝 动态数量")]:
            card = card_frame()
            card.setProperty("kpiColor", admin_kpi_colors.get(key, "blue"))
            c = QVBoxLayout(card)
            t = QLabel(title)
            t.setObjectName("kpiTitle")
            v = QLabel("0")
            v.setObjectName("kpiValue")
            c.addWidget(t)
            c.addWidget(v)
            cards.addWidget(card)
            self.admin_kpi_labels[key] = v
        layout.addLayout(cards)
        chart_card = card_frame()
        chart_layout = QVBoxLayout(chart_card)
        title = QLabel("近一周场馆预约热度")
        title.setObjectName("sectionTitle")
        self.admin_chart = BarChart()
        chart_layout.addWidget(title)
        chart_layout.addWidget(self.admin_chart)
        layout.addWidget(chart_card, 1)
        self.admin_recent_logs = QTextEdit()
        self.admin_recent_logs.setReadOnly(True)
        layout.addWidget(self._text_card("最近管理操作", self.admin_recent_logs), 1)
        return page

    def _build_admin_users(self) -> QWidget:
        page, layout = self._content_page("用户管理", "查看使用者并执行封禁、解封。")
        tools = QHBoxLayout()
        refresh = set_secondary(QPushButton("刷新"))
        refresh.clicked.connect(self.refresh_admin_users)
        ban = set_danger(QPushButton("封禁用户"))
        ban.clicked.connect(lambda: self.admin_change_user("banned"))
        unban = set_primary(QPushButton("解封用户"))
        unban.clicked.connect(lambda: self.admin_change_user("active"))
        tools.addStretch(1)
        tools.addWidget(refresh)
        tools.addWidget(ban)
        tools.addWidget(unban)
        layout.addLayout(tools)
        self.admin_user_table = self._table(["账号", "姓名", "身份", "状态", "学院/单位", "创建时间"])
        self.admin_user_table.itemSelectionChanged.connect(lambda: self.capture_admin_selection("user", self.admin_user_rows, self.admin_user_table))
        layout.addWidget(self.admin_user_table, 1)
        return page

    def _build_admin_products(self) -> QWidget:
        page, layout = self._content_page("商品管理", "下架违规商品或恢复误操作商品。")
        tools = QHBoxLayout()
        refresh = set_secondary(QPushButton("刷新"))
        refresh.clicked.connect(self.refresh_admin_products)
        detail = set_secondary(QPushButton("查看详情"))
        detail.clicked.connect(self.admin_show_product_detail)
        remove = set_danger(QPushButton("下架商品"))
        remove.clicked.connect(lambda: self.admin_change_product("removed"))
        restore = set_primary(QPushButton("恢复商品"))
        restore.clicked.connect(lambda: self.admin_change_product("normal"))
        tools.addStretch(1)
        tools.addWidget(refresh)
        tools.addWidget(detail)
        tools.addWidget(remove)
        tools.addWidget(restore)
        layout.addLayout(tools)
        self.admin_product_table = self._table(["标题", "分类", "校区", "价格", "发布人", "状态", "发布时间"])
        self.admin_product_table.itemSelectionChanged.connect(lambda: self.capture_admin_selection("product", self.admin_product_rows, self.admin_product_table))
        layout.addWidget(self.admin_product_table, 1)
        return page

    def _build_admin_bookings(self) -> QWidget:
        page, layout = self._content_page("预约管理", "查看所有预约并执行后台强制取消。")
        tools = QHBoxLayout()
        refresh = set_secondary(QPushButton("刷新"))
        refresh.clicked.connect(self.refresh_admin_bookings)
        cancel = set_danger(QPushButton("强制取消预约"))
        cancel.clicked.connect(self.admin_cancel_booking)
        tools.addStretch(1)
        tools.addWidget(refresh)
        tools.addWidget(cancel)
        layout.addLayout(tools)
        self.admin_booking_table = self._table(["用户", "账号", "场馆", "地点", "日期", "时段", "状态"])
        self.admin_booking_table.itemSelectionChanged.connect(lambda: self.capture_admin_selection("booking", self.admin_booking_rows, self.admin_booking_table))
        layout.addWidget(self.admin_booking_table, 1)
        return page

    def _build_admin_activities(self) -> QWidget:
        page, layout = self._content_page("活动管理", "查看活动、取消活动、导出报名名单。")
        tools = QHBoxLayout()
        refresh = set_secondary(QPushButton("刷新"))
        refresh.clicked.connect(self.refresh_admin_activities)
        detail = set_secondary(QPushButton("查看详情"))
        detail.clicked.connect(self.admin_show_activity_detail)
        cancel = set_danger(QPushButton("取消活动"))
        cancel.clicked.connect(self.admin_cancel_activity)
        export = set_primary(QPushButton("导出名单"))
        export.clicked.connect(self.admin_export_activity)
        tools.addStretch(1)
        tools.addWidget(refresh)
        tools.addWidget(detail)
        tools.addWidget(cancel)
        tools.addWidget(export)
        layout.addLayout(tools)
        self.admin_activity_table = self._table(["标题", "分类", "组织者", "时间", "地点", "报名数", "状态"])
        self.admin_activity_table.itemSelectionChanged.connect(lambda: self.capture_admin_selection("activity", self.admin_activity_rows, self.admin_activity_table))
        layout.addWidget(self.admin_activity_table, 1)
        return page

    def _build_admin_moments(self) -> QWidget:
        page, layout = self._content_page("生活圈审核", "删除违规动态或恢复误删动态。")
        tools = QHBoxLayout()
        refresh = set_secondary(QPushButton("刷新"))
        refresh.clicked.connect(self.refresh_admin_moments)
        detail = set_secondary(QPushButton("查看详情"))
        detail.clicked.connect(self.admin_show_moment_detail)
        remove = set_danger(QPushButton("删除动态"))
        remove.clicked.connect(lambda: self.admin_change_moment("removed"))
        restore = set_primary(QPushButton("恢复动态"))
        restore.clicked.connect(lambda: self.admin_change_moment("normal"))
        tools.addStretch(1)
        tools.addWidget(refresh)
        tools.addWidget(detail)
        tools.addWidget(remove)
        tools.addWidget(restore)
        layout.addLayout(tools)
        self.admin_moment_table = self._table(["分类", "发布人", "内容", "点赞", "评论", "状态", "发布时间"])
        self.admin_moment_table.itemSelectionChanged.connect(lambda: self.capture_admin_selection("moment", self.admin_moment_rows, self.admin_moment_table))
        layout.addWidget(self.admin_moment_table, 1)
        return page

    def _build_admin_logs(self) -> QWidget:
        page, layout = self._content_page("操作日志", "所有后台关键操作均保留记录。")
        refresh = set_secondary(QPushButton("刷新"))
        refresh.clicked.connect(self.refresh_admin_logs)
        layout.addWidget(refresh, 0, Qt.AlignRight)
        self.admin_log_table = self._table(["管理员", "操作", "对象", "对象ID", "详情", "时间"])
        layout.addWidget(self.admin_log_table, 1)
        return page

    def _table(self, headers: list[str]) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setShowGrid(False)
        table.setFrameStyle(QFrame.NoFrame)
        return table

    def fill_table(self, table: QTableWidget, rows: list[list[str]], status_column: int | None = None, seat_column: int | None = None) -> None:
        if not rows:
            table.setRowCount(1)
            table.setSpan(0, 0, 1, table.columnCount())
            empty_item = QTableWidgetItem("暂无数据")
            empty_item.setTextAlignment(Qt.AlignCenter)
            empty_item.setForeground(QColor("#9CA3AF"))
            table.setItem(0, 0, empty_item)
            return
        table.setRowCount(len(rows))
        for r, values in enumerate(rows):
            row_status = values[status_column] if status_column is not None and status_column < len(values) else ""
            for c, value in enumerate(values):
                item = QTableWidgetItem(value)
                if status_column is not None and c == status_column:
                    if "正常" in value or "成功" in value:
                        item.setForeground(QColor("#00A896"))
                    elif "封禁" in value or "下架" in value or "强制" in value or "取消" in value:
                        item.setForeground(QColor("#E63946" if "封禁" in value or "下架" in value else "#6C757D"))
                        if "强制" in value:
                            font = item.font()
                            font.setItalic(True)
                            item.setFont(font)
                # 余量/余座数字颜色区分
                if seat_column is not None and c == seat_column:
                    try:
                        seats = int(value)
                        if seats > 5:
                            item.setForeground(QColor("#10B981"))
                        elif seats > 0:
                            item.setForeground(QColor("#F59E0B"))
                        else:
                            item.setForeground(QColor("#EF4444"))
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)
                    except ValueError:
                        pass
                if "封禁" in row_status or "下架" in row_status or "删除" in row_status:
                    item.setBackground(QColor("#F1F3F5"))
                table.setItem(r, c, item)
        if rows:
            table.selectRow(0)

    def refresh_user_all(self) -> None:
        self.refresh_home()
        self.refresh_market()
        self.refresh_bookings()
        self.refresh_buses()
        self.refresh_activities()
        self.refresh_moments()
        self.refresh_profile()

    def refresh_home(self) -> None:
        summary = self.model.dashboard_summary()
        for key, value in summary["totals"].items():
            animate_number_count(self.user_kpi_labels[key], value)
        products_html = "".join(
            f'<div style="border-bottom:1px solid #E8ECF1;padding:10px 0;">'
            f'<div><b style="color:#C9A962;font-size:15px;">🛍 {p["title"]}</b> '
            f'<span style="color:#E74C3C;font-weight:bold;font-size:15px;">¥{p["price"]:.0f}</span></div>'
            f'<div style="color:#6B7280;font-size:13px;margin-top:4px;">{p["seller_name"]} · {p.get("category", "")}</div>'
            f'</div>'
            for p in summary["recent_products"]
        ) or '<div style="color:#9CA3AF;padding:20px;text-align:center;">暂无商品</div>'
        self.home_products.setHtml(products_html)
        activities_html = "".join(
            f'<div style="border-bottom:1px solid #E8ECF1;padding:10px 0;">'
            f'<div><b style="color:#1A1A2E;font-size:15px;">🎉 {a["title"]}</b></div>'
            f'<div style="color:#6B7280;font-size:13px;margin-top:4px;">'
            f'🕐 {a["start_time"]} · 📍 {a["location"]} · 📁 {a.get("category", "")}</div>'
            f'</div>'
            for a in summary["recent_activities"]
        ) or '<div style="color:#9CA3AF;padding:20px;text-align:center;">暂无活动</div>'
        self.home_activities.setHtml(activities_html)

    def clear_grid(self, grid: QGridLayout) -> None:
        while grid.count():
            item = grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def refresh_market(self) -> None:
        self.market_rows = self.model.list_products(self.market_keyword.text().strip(), self.market_category.currentText())
        self.clear_grid(self.market_grid)
        for index, product in enumerate(self.market_rows):
            card = card_frame()
            card.setMinimumHeight(260)
            layout = QVBoxLayout(card)
            layout.setSpacing(8)
            layout.setContentsMargins(12, 12, 12, 12)
            img = QLabel()
            img.setPixmap(product_pixmap(product["image_path"], 260, 120, product.get("category", ""), product.get("title", "")))
            img.setFixedHeight(120)
            img.setAlignment(Qt.AlignCenter)
            title = QLabel(product["title"])
            title.setObjectName("cardTitle")
            title.setWordWrap(True)
            price = QLabel(f"¥{product['price']:.2f}")
            price.setObjectName("priceText")
            meta = QLabel(f"{product['category']} · {product['campus']} · {product['seller_name']}")
            meta.setObjectName("mutedText")
            meta.setWordWrap(True)
            btn = set_secondary(QPushButton("留言 / 详情"))
            btn.clicked.connect(lambda _checked=False, pid=product["id"]: self.open_product_detail(pid))
            layout.addWidget(img)
            layout.addWidget(title)
            layout.addWidget(price)
            layout.addWidget(meta)
            layout.addStretch(1)
            layout.addWidget(btn)
            self.market_grid.addWidget(card, index // 3, index % 3)

    def open_product_dialog(self) -> None:
        dialog = ProductDialog(self, self.model)
        if dialog.exec() != QDialog.Accepted:
            return
        ok, msg = self.model.create_product(
            dialog.title_input.text().strip(),
            dialog.category_input.currentText(),
            dialog.campus_input.currentText(),
            dialog.price_input.text().strip(),
            dialog.desc_input.toPlainText().strip(),
            dialog.image_path,
        )
        self.show_toast(msg, ok)
        if ok:
            self.refresh_home()
            self.refresh_market()

    def open_product_detail(self, product_id: int) -> None:
        detail = self.model.get_product(product_id)
        if detail is None:
            self.show_toast("商品不存在", False)
            return
        dialog = DetailDialog(
            self,
            detail["title"],
            f"{detail['category']} · {detail['campus']} · {detail['seller_name']}",
            STATUS_LABELS.get(detail["status"], detail["status"]),
            detail["status"],
        )
        image = QLabel()
        image.setPixmap(product_pixmap(detail["image_path"], 650, 180, detail.get("category", ""), detail.get("title", "")))
        image.setFixedHeight(180)
        image.setAlignment(Qt.AlignCenter)
        dialog.root.addWidget(image)
        dialog.add_meta_grid([
            ("价格", f"¥{detail['price']:.2f}"),
            ("卖家", detail["seller_name"]),
            ("校区", detail["campus"]),
            ("单位", detail["seller_college"]),
        ])
        dialog.add_section("商品描述", detail["description"], 80)
        history = "\n".join(f"[{m['created_at']}] {m['display_name']}: {m['content']}" for m in detail["messages"]) or "暂无留言"
        dialog.add_section("留言记录", history, 110)

        def leave_message() -> None:
            message_dialog = CommentDialog(dialog, "商品留言", "给卖家留一句话")
            if message_dialog.exec() != QDialog.Accepted:
                return
            ok, msg = self.model.add_product_message(product_id, message_dialog.content_input.toPlainText().strip())
            self.show_toast(msg, ok)
            if ok:
                dialog.accept()

        dialog.add_actions([
            ("返回列表", dialog.reject, "secondary"),
            ("我要留言", leave_message, "primary"),
        ])
        if dialog.exec() == QDialog.Accepted:
            self.refresh_market()

    def refresh_bookings(self) -> None:
        self.slot_rows = self.model.list_slots(self.booking_category.currentText())
        self.fill_table(
            self.slot_table,
            [[r["name"], r["category"], r["campus"], r["location"], r["slot_date"], r["slot_time"], str(r["seats_left"])] for r in self.slot_rows],
            seat_column=6,
        )
        self.booking_rows = self.model.list_my_bookings()
        self.fill_table(
            self.booking_table,
            [[r["name"], r["location"], r["slot_date"], r["slot_time"], STATUS_LABELS.get(r["status"], r["status"])] for r in self.booking_rows],
            4,
        )
        # 为场馆表格第一列添加场馆图标
        venue_icons = {"羽毛球场": "🏸", "篮球场": "🏀", "足球场": "⚽", "游泳池": "🏊", "乒乓球室": "🏓", "网球场": "🎾"}
        for row in range(self.slot_table.rowCount()):
            item = self.slot_table.item(row, 0)
            if item:
                venue_name = item.text()
                emoji = "🏟️"
                for key, e in venue_icons.items():
                    if key in venue_name:
                        emoji = e
                        break
                ic = QPixmap(24, 24)
                ic.fill(QColor("#10B981"))
                p = QPainter(ic)
                p.setRenderHint(QPainter.Antialiasing)
                p.setPen(QColor("#FFFFFF"))
                p.setFont(QFont("Segoe UI Emoji", 14))
                p.drawText(ic.rect(), Qt.AlignCenter, emoji)
                p.end()
                item.setIcon(ic)

    def capture_slot_selection(self) -> None:
        row = self.slot_table.currentRow()
        self.current_slot_id = self.slot_rows[row]["id"] if 0 <= row < len(getattr(self, "slot_rows", [])) else None

    def capture_booking_selection(self) -> None:
        row = self.booking_table.currentRow()
        self.current_booking_id = self.booking_rows[row]["id"] if 0 <= row < len(getattr(self, "booking_rows", [])) else None

    def create_booking(self) -> None:
        slot_id = getattr(self, "current_slot_id", None)
        if slot_id is None:
            self.show_toast("请先选择时段", False)
            return
        row = self.slot_table.currentRow()
        slot = self.slot_rows[row] if 0 <= row < len(getattr(self, "slot_rows", [])) else None
        if slot is not None:
            confirm = ConfirmDialog(
                self,
                "确认预约",
                f"场馆：{slot['name']}\n地点：{slot['location']}\n日期：{slot['slot_date']}\n时段：{slot['slot_time']}\n\n确认提交后会占用该时段名额。",
            )
            if confirm.exec() != QDialog.Accepted:
                return
        ok, msg = self.model.create_booking(slot_id)
        self.show_toast(msg, ok)
        if ok:
            self.refresh_home()
            self.refresh_bookings()
            self.refresh_profile()

    def cancel_booking(self) -> None:
        if self.current_booking_id is None:
            self.show_toast("请先选择预约记录", False)
            return
        confirm = ConfirmDialog(self, "取消预约", "确认取消选中的预约记录？取消后该时段名额会释放。", True)
        if confirm.exec() != QDialog.Accepted:
            return
        ok, msg = self.model.cancel_booking(self.current_booking_id)
        self.show_toast(msg, ok)
        if ok:
            self.refresh_home()
            self.refresh_bookings()
            self.refresh_profile()

    def refresh_buses(self) -> None:
        self.bus_rows = self.model.list_shuttle_routes(self.bus_campus.currentText())
        self.fill_table(
            self.bus_table,
            [[r["route_name"], r["from_campus"], r["to_campus"], r["station"], r["departure_time"], str(r["seats_left"])] for r in self.bus_rows],
            seat_column=5,
        )
        # 为校车表格第一列添加巴士图标
        bus_icon = QPixmap(24, 24)
        bus_icon.fill(QColor("#3B82F6"))
        bp = QPainter(bus_icon)
        bp.setRenderHint(QPainter.Antialiasing)
        bp.setPen(QColor("#FFFFFF"))
        bp.setFont(QFont("Segoe UI Emoji", 14))
        bp.drawText(bus_icon.rect(), Qt.AlignCenter, "🚌")
        bp.end()
        for row in range(self.bus_table.rowCount()):
            item = self.bus_table.item(row, 0)
            if item:
                item.setIcon(bus_icon)
        tickets = self.model.list_my_tickets()
        if tickets:
            tickets_html = "".join(
                f'<div style="border-bottom:1px solid #E8ECF1; padding:10px 0;">'
                f'<div><b style="color:#1A1A2E; font-size:15px;">{t["route_name"]}</b></div>'
                f'<div style="color:#6B7280; font-size:13px; margin-top:4px;">'
                f'📅 {t["ride_date"]} {t["departure_time"]} · 📍 {t["station"]}</div>'
                f'</div>'
                for t in tickets
            )
        else:
            tickets_html = '<div style="color:#9CA3AF; padding:20px; text-align:center;">暂无车票</div>'
        self.ticket_text.setHtml(tickets_html)

    def capture_route_selection(self) -> None:
        row = self.bus_table.currentRow()
        self.current_route_id = self.bus_rows[row]["id"] if 0 <= row < len(getattr(self, "bus_rows", [])) else None

    def create_ticket(self) -> None:
        if self.current_route_id is None:
            self.show_toast("请先选择班次", False)
            return
        row = self.bus_table.currentRow()
        route = self.bus_rows[row] if 0 <= row < len(getattr(self, "bus_rows", [])) else None
        if route is not None:
            confirm = ConfirmDialog(
                self,
                "确认购票",
                f"线路：{route['route_name']}\n乘车点：{route['station']}\n发车时间：{route['departure_time']}\n余座：{route['seats_left']}\n\n确认后将生成今日校车票。",
            )
            if confirm.exec() != QDialog.Accepted:
                return
        ok, msg = self.model.create_shuttle_ticket(self.current_route_id)
        self.show_toast(msg, ok)
        if ok:
            self.refresh_buses()
            self.refresh_profile()

    def refresh_activities(self) -> None:
        self.activity_rows = self.model.list_activities(self.activity_category.currentText())
        self.fill_table(
            self.activity_table,
            [[r["title"], r["category"], r["organizer_name"], r["start_time"], r["location"], str(r["seats_left"]), STATUS_LABELS.get(r["status"], r["status"])] for r in self.activity_rows],
            6,
            seat_column=5,
        )
        self.open_activity_detail()

    def open_activity_detail(self) -> None:
        row = self.activity_table.currentRow()
        if not (0 <= row < len(getattr(self, "activity_rows", []))):
            self.current_activity_id = None
            self.activity_detail.clear()
            return
        self.current_activity_id = self.activity_rows[row]["id"]
        detail = self.model.get_activity(self.current_activity_id)
        if detail is None:
            return
        ratio = detail['registered_count'] / detail['capacity'] if detail['capacity'] > 0 else 0
        bar_color = "#27AE60" if ratio < 0.7 else "#E74C3C" if ratio >= 0.95 else "#C9A962"
        self.activity_detail.setHtml(
            f'<div style="padding:8px 0;">'
            f'<div style="font-size:18px; font-weight:bold; color:#1A1A2E;">🎉 {detail["title"]}</div>'
            f'<div style="color:#6B7280; font-size:13px; margin-top:12px; line-height:1.7;">{detail["summary"]}</div>'
            f'<div style="margin-top:16px; padding:12px; background:#FAFBFD; border-radius:8px;">'
            f'<div style="color:#6B7280; font-size:13px; margin-bottom:8px;">报名进度</div>'
            f'<div style="background:#E8ECF1; border-radius:6px; height:8px; overflow:hidden;">'
            f'<div style="background:{bar_color}; width:{min(ratio * 100, 100):.0f}%; height:100%; border-radius:6px;"></div>'
            f'</div>'
            f'<div style="color:#1A1A2E; font-weight:bold; margin-top:6px; font-size:14px;">'
            f'{detail["registered_count"]} / {detail["capacity"]} 人已报名</div>'
            f'</div></div>'
        )

    def show_activity_detail_dialog(self) -> bool:
        if self.current_activity_id is None:
            self.show_toast("请先选择活动", False)
            return False
        detail = self.model.get_activity(self.current_activity_id)
        if detail is None:
            self.show_toast("活动不存在", False)
            return False
        dialog = DetailDialog(
            self,
            detail["title"],
            f"{detail['category']} · {detail['organizer_name']}",
            STATUS_LABELS.get(detail["status"], detail["status"]),
            detail["status"],
        )
        dialog.add_meta_grid([
            ("时间", detail["start_time"]),
            ("地点", detail["location"]),
            ("报名", f"{detail['registered_count']} / {detail['capacity']}"),
            ("剩余", str(detail["seats_left"])),
        ])
        dialog.add_section("活动简介", detail["summary"], 100)
        members = "\n".join(f"{m['display_name']} / {m['college']}" for m in detail["members"]) or "暂无报名成员"
        dialog.add_section("报名成员", members, 130)
        accepted = {"value": False}

        def confirm_join() -> None:
            confirm = ConfirmDialog(dialog, "确认报名", f"确认报名参加「{detail['title']}」？\n系统会记录你的报名信息。")
            if confirm.exec() != QDialog.Accepted:
                return
            accepted["value"] = True
            dialog.accept()

        dialog.add_actions([
            ("关闭", dialog.reject, "secondary"),
            ("报名活动", confirm_join, "primary"),
        ])
        dialog.exec()
        return accepted["value"]

    def register_activity(self) -> None:
        if self.current_activity_id is None:
            self.show_toast("请先选择活动", False)
            return
        if not self.show_activity_detail_dialog():
            return
        ok, msg = self.model.register_activity(self.current_activity_id)
        self.show_toast(msg, ok)
        if ok:
            self.refresh_home()
            self.refresh_activities()
            self.refresh_profile()

    def open_activity_dialog(self) -> None:
        dialog = ActivityDialog(self, self.model)
        if dialog.exec() != QDialog.Accepted:
            return
        ok, msg = self.model.create_activity(
            dialog.title_input.text().strip(),
            dialog.category_input.currentText(),
            dialog.location_input.text().strip(),
            dialog.time_input.text().strip(),
            dialog.capacity_input.text().strip(),
            dialog.summary_input.toPlainText().strip(),
        )
        self.show_toast(msg, ok)
        if ok:
            self.refresh_home()
            self.refresh_activities()

    def export_activity(self) -> None:
        if self.current_activity_id is None:
            self.show_toast("请先选择活动", False)
            return
        confirm = ConfirmDialog(self, "导出报名名单", "将当前活动报名名单导出到 data/exports 目录，确认继续？")
        if confirm.exec() != QDialog.Accepted:
            return
        target = self.model.export_activity_csv(self.current_activity_id)
        self.show_toast(f"名单已导出：{target}" if target else "导出失败", bool(target))

    def refresh_moments(self) -> None:
        self.moment_rows = self.model.list_moments(self.moment_category.currentText())
        self.moment_list.clear()
        for row in self.moment_rows:
            item = QListWidgetItem(f"[{row['category']}] {row['display_name']}  {row['created_at']}\n♥ {row['like_count']}   评论 {row['comment_count']}\n{row['content'][:70]}")
            item.setData(Qt.UserRole, row["id"])
            # 添加分类图标
            img_file = MOMENT_CATEGORY_IMAGES.get(row["category"], "")
            if img_file:
                img_path = ASSETS_DIR / img_file
                if img_path.exists():
                    pix = QPixmap(str(img_path)).scaled(48, 48, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    item.setIcon(pix)
            self.moment_list.addItem(item)
        if self.moment_rows:
            self.moment_list.setCurrentRow(0)
        else:
            self.current_moment_id = None
            self.moment_detail.clear()

    def open_moment_detail(self) -> None:
        current = self.moment_list.currentItem()
        if current is None:
            return
        self.current_moment_id = int(current.data(Qt.UserRole))
        detail = self.model.get_moment(self.current_moment_id)
        if detail is None:
            return
        if detail["comments"]:
            comments_html = "".join(
                f'<div style="border-bottom:1px solid #E8ECF1; padding:10px 0;">'
                f'<div style="color:#6B7280; font-size:12px;">'
                f'<b style="color:#1A1A2E;">{c["display_name"]}</b> · {c["created_at"]}</div>'
                f'<div style="margin-top:4px; color:#1A1A2E;">{c["content"]}</div>'
                f'</div>'
                for c in detail["comments"]
            )
        else:
            comments_html = '<div style="color:#9CA3AF; padding:16px; text-align:center;">暂无评论</div>'
        self.moment_detail.setHtml(
            f'<div style="padding:8px 0;">'
            f'<table style="width:100%; margin-bottom:12px;"><tr>'
            f'<td style="color:#6B7280; font-size:13px; padding-right:16px;">👤 {detail["display_name"]}</td>'
            f'<td style="color:#6B7280; font-size:13px; padding-right:16px;">📁 {detail["category"]}</td>'
            f'<td style="color:#6B7280; font-size:13px; padding-right:16px;">🕐 {detail["created_at"]}</td>'
            f'<td style="color:#6B7280; font-size:13px; padding-right:16px;">❤️ {detail["like_count"]}</td>'
            f'<td style="color:#6B7280; font-size:13px;">💬 {detail["comment_count"]}</td>'
            f'</tr></table>'
            f'<div style="color:#1A1A2E; font-size:14px; line-height:1.8; margin:16px 0; padding:12px; background:#FAFBFD; border-radius:8px;">'
            f'{detail["content"]}</div>'
            f'<div style="border-top:2px solid #C9A962; padding-top:12px; margin-top:16px;">'
            f'<div style="font-weight:bold; color:#C9A962; margin-bottom:8px;">评论区</div>'
            f'{comments_html}</div></div>'
        )

    def show_moment_detail_dialog(self) -> bool:
        if self.current_moment_id is None:
            self.show_toast("请先选择动态", False)
            return False
        detail = self.model.get_moment(self.current_moment_id)
        if detail is None:
            self.show_toast("动态不存在", False)
            return False
        dialog = DetailDialog(
            self,
            detail["category"],
            f"{detail['display_name']} · {detail['created_at']}",
            STATUS_LABELS.get(detail["status"], detail["status"]),
            detail["status"],
        )
        dialog.add_meta_grid([
            ("点赞", str(detail["like_count"])),
            ("评论", str(detail["comment_count"])),
            ("作者", detail["display_name"]),
            ("时间", detail["created_at"]),
        ])
        dialog.add_section("动态内容", detail["content"], 120)
        comments = "\n".join(f"[{c['created_at']}] {c['display_name']}: {c['content']}" for c in detail["comments"]) or "暂无评论"
        dialog.add_section("评论区", comments, 150)
        comment_requested = {"value": False}

        def add_comment() -> None:
            comment_requested["value"] = True
            dialog.accept()

        dialog.add_actions([
            ("关闭", dialog.reject, "secondary"),
            ("去评论", add_comment, "primary"),
        ])
        dialog.exec()
        return comment_requested["value"]

    def open_moment_dialog(self) -> None:
        dialog = MomentDialog(self, self.model)
        if dialog.exec() != QDialog.Accepted:
            return
        ok, msg = self.model.create_moment(dialog.category_input.currentText(), dialog.content_input.toPlainText().strip(), dialog.image_path)
        self.show_toast(msg, ok)
        if ok:
            self.refresh_home()
            self.refresh_moments()
            self.refresh_profile()

    def toggle_like(self) -> None:
        if self.current_moment_id is None:
            self.show_toast("请先选择动态", False)
            return
        ok, msg = self.model.toggle_like(self.current_moment_id)
        self.show_toast(msg, ok)
        if ok:
            self.refresh_moments()

    def open_comment_dialog(self) -> None:
        if self.current_moment_id is None:
            self.show_toast("请先选择动态", False)
            return
        if not self.show_moment_detail_dialog():
            return
        dialog = CommentDialog(self, "发表评论", "补充你的评论")
        if dialog.exec() != QDialog.Accepted:
            return
        ok, msg = self.model.add_comment(self.current_moment_id, dialog.content_input.toPlainText().strip())
        self.show_toast(msg, ok)
        if ok:
            self.refresh_moments()

    def refresh_profile(self) -> None:
        data = self.model.profile_data()
        user = data["user"]
        bookings_html = "".join(
            f'<div style="border-bottom:1px solid #E8ECF1; padding:8px 0;">'
            f'<b style="color:#1A1A2E;">{b["name"]}</b> '
            f'<span style="color:#6B7280;">{b["slot_date"]} {b["slot_time"]}</span> '
            f'<span style="color:{"#27AE60" if b["status"] == "normal" else "#E74C3C"}; font-weight:bold;">'
            f'{STATUS_LABELS.get(b["status"], b["status"])}</span></div>'
            for b in data["bookings"]
        ) or '<div style="color:#9CA3AF; padding:12px; text-align:center;">暂无预约</div>'
        tickets_html = "".join(
            f'<div style="border-bottom:1px solid #E8ECF1; padding:8px 0;">'
            f'<b style="color:#1A1A2E;">{t["route_name"]}</b> '
            f'<span style="color:#6B7280;">{t["ride_date"]} {t["departure_time"]}</span></div>'
            for t in data["tickets"]
        ) or '<div style="color:#9CA3AF; padding:12px; text-align:center;">暂无车票</div>'
        self.profile_text.setHtml(
            f'<div style="padding:4px 0;">'
            f'<table style="width:100%; border-collapse:collapse;">'
            f'<tr><td style="color:#6B7280; padding:6px 12px 6px 0; font-size:13px; width:100px;">姓名</td>'
            f'<td style="font-weight:bold; padding:6px 0;">{user["display_name"]}</td></tr>'
            f'<tr><td style="color:#6B7280; padding:6px 12px 6px 0; font-size:13px;">账号</td>'
            f'<td style="padding:6px 0;">{user["username"]}</td></tr>'
            f'<tr><td style="color:#6B7280; padding:6px 12px 6px 0; font-size:13px;">身份</td>'
            f'<td style="padding:6px 0;">{ROLE_LABELS.get(user["role"], user["role"])}</td></tr>'
            f'<tr><td style="color:#6B7280; padding:6px 12px 6px 0; font-size:13px;">学院</td>'
            f'<td style="padding:6px 0;">{user["college"]}</td></tr>'
            f'<tr><td style="color:#6B7280; padding:6px 12px 6px 0; font-size:13px;">注册时间</td>'
            f'<td style="padding:6px 0;">{user["created_at"]}</td></tr>'
            f'</table>'
            f'<table style="width:100%; margin:16px 0; padding:12px; background:#FAFBFD; border-radius:8px; border-collapse:separate; border-spacing:24px 0;"><tr>'
            f'<td style="text-align:center;"><div style="font-size:20px; font-weight:bold; color:#C9A962;">{data["product_count"]}</div>'
            f'<div style="color:#6B7280; font-size:12px;">在售商品</div></td>'
            f'<td style="text-align:center;"><div style="font-size:20px; font-weight:bold; color:#C9A962;">{data["moment_count"]}</div>'
            f'<div style="color:#6B7280; font-size:12px;">生活圈动态</div></td></tr></table>'
            f'<div style="margin-top:16px;"><div style="font-weight:bold; color:#C9A962; margin-bottom:8px;">预约记录</div>'
            f'{bookings_html}</div>'
            f'<div style="margin-top:16px;"><div style="font-weight:bold; color:#C9A962; margin-bottom:8px;">车票记录</div>'
            f'{tickets_html}</div></div>'
        )

    def change_password(self) -> None:
        if self.new_password.text() != self.confirm_password.text():
            self.show_toast("两次新密码不一致", False)
            return
        ok, msg = self.model.update_password(self.old_password.text(), self.new_password.text())
        self.show_toast(msg, ok)
        if ok:
            self.old_password.clear()
            self.new_password.clear()
            self.confirm_password.clear()

    def refresh_admin_all(self) -> None:
        self.refresh_admin_overview()
        self.refresh_admin_users()
        self.refresh_admin_products()
        self.refresh_admin_bookings()
        self.refresh_admin_activities()
        self.refresh_admin_moments()
        self.refresh_admin_logs()

    def refresh_admin_overview(self) -> None:
        summary = self.model.admin_summary()
        for key, value in summary["totals"].items():
            animate_number_count(self.admin_kpi_labels[key], value)
        self.admin_chart.set_data(summary["venue_hot"])
        logs = summary["recent_logs"]
        if logs:
            logs_html = "".join(
                f'<div style="border-bottom:1px solid #E8ECF1; padding:10px 0;">'
                f'<div style="color:#9CA3AF; font-size:12px;">{l["created_at"]}</div>'
                f'<div style="margin-top:4px;"><b style="color:#1A1A2E;">{l["admin_name"]}</b> '
                f'<span style="color:#C9A962; font-weight:bold;">{l["action"]}</span></div>'
                f'<div style="color:#6B7280; font-size:13px; margin-top:2px;">{l["detail"]}</div>'
                f'</div>'
                for l in logs
            )
        else:
            logs_html = '<div style="color:#9CA3AF; padding:20px; text-align:center;">暂无操作日志</div>'
        self.admin_recent_logs.setHtml(logs_html)

    def capture_admin_selection(self, key: str, rows: list[dict], table: QTableWidget) -> None:
        row = table.currentRow()
        self.current_admin_ids[key] = rows[row]["id"] if 0 <= row < len(rows) else None

    def refresh_admin_users(self) -> None:
        self.admin_user_rows = self.model.admin_users()
        self.fill_table(
            self.admin_user_table,
            [[r["username"], r["display_name"], ROLE_LABELS.get(r["role"], r["role"]), STATUS_LABELS.get(r["status"], r["status"]), r["college"], r["created_at"]] for r in self.admin_user_rows],
            3,
        )

    def admin_change_user(self, status: str) -> None:
        user_id = self.current_admin_ids.get("user")
        if user_id is None:
            self.show_toast("请先选择用户", False)
            return
        row = next((item for item in self.admin_user_rows if item["id"] == user_id), None)
        action = "解封用户" if status == "active" else "封禁用户"
        reason = ""
        if row is not None:
            dialog = ReasonDialog(
                self,
                action,
                f"账号：{row['username']}\n姓名：{row['display_name']}\n身份：{ROLE_LABELS.get(row['role'], row['role'])}\n当前状态：{STATUS_LABELS.get(row['status'], row['status'])}",
                "填写处理依据，例如违规发布、误封恢复等",
            )
            if dialog.exec() != QDialog.Accepted:
                return
            reason = dialog.reason()
        ok, msg = self.model.admin_set_user_status(user_id, status, reason)
        self.show_toast(msg, ok)
        if ok:
            self.refresh_admin_users()
            self.refresh_admin_overview()
            self.refresh_admin_logs()

    def refresh_admin_products(self) -> None:
        self.admin_product_rows = self.model.admin_products()
        self.fill_table(
            self.admin_product_table,
            [[r["title"], r["category"], r["campus"], f"¥{r['price']:.2f}", r["seller_name"], STATUS_LABELS.get(r["status"], r["status"]), r["created_at"]] for r in self.admin_product_rows],
            5,
        )

    def admin_change_product(self, status: str) -> None:
        product_id = self.current_admin_ids.get("product")
        if product_id is None:
            self.show_toast("请先选择商品", False)
            return
        row = next((item for item in self.admin_product_rows if item["id"] == product_id), None)
        action = "恢复商品" if status == "normal" else "下架商品"
        reason = ""
        if row is not None:
            dialog = ReasonDialog(
                self,
                action,
                f"商品：{row['title']}\n分类：{row['category']}\n发布人：{row['seller_name']}\n当前状态：{STATUS_LABELS.get(row['status'], row['status'])}",
                "填写处理原因，例如信息违规、交易完成、误操作恢复等",
            )
            if dialog.exec() != QDialog.Accepted:
                return
            reason = dialog.reason()
        ok, msg = self.model.admin_set_product_status(product_id, status, reason)
        self.show_toast(msg, ok)
        if ok:
            self.refresh_admin_products()
            self.refresh_admin_overview()
            self.refresh_admin_logs()

    def admin_show_product_detail(self) -> None:
        product_id = self.current_admin_ids.get("product")
        if product_id is None:
            self.show_toast("请先选择商品", False)
            return
        detail = self.model.get_product(product_id)
        if detail is None:
            self.show_toast("商品不存在", False)
            return
        dialog = DetailDialog(
            self,
            detail["title"],
            f"{detail['category']} · {detail['campus']} · {detail['seller_name']}",
            STATUS_LABELS.get(detail["status"], detail["status"]),
            detail["status"],
        )
        dialog.add_meta_grid([
            ("价格", f"¥{detail['price']:.2f}"),
            ("发布人", detail["seller_name"]),
            ("校区", detail["campus"]),
            ("发布时间", detail["created_at"]),
        ])
        dialog.add_section("商品描述", detail["description"], 100)
        messages = "\n".join(f"[{m['created_at']}] {m['display_name']}: {m['content']}" for m in detail["messages"]) or "暂无留言"
        dialog.add_section("留言记录", messages, 130)
        dialog.add_actions([("关闭", dialog.reject, "secondary")])
        dialog.exec()

    def refresh_admin_bookings(self) -> None:
        self.admin_booking_rows = self.model.admin_bookings()
        self.fill_table(
            self.admin_booking_table,
            [[r["display_name"], r["username"], r["name"], r["location"], r["slot_date"], r["slot_time"], STATUS_LABELS.get(r["status"], r["status"])] for r in self.admin_booking_rows],
            6,
        )

    def admin_cancel_booking(self) -> None:
        booking_id = self.current_admin_ids.get("booking")
        if booking_id is None:
            self.show_toast("请先选择预约", False)
            return
        row = next((item for item in self.admin_booking_rows if item["id"] == booking_id), None)
        reason = ""
        if row is not None:
            dialog = ReasonDialog(
                self,
                "强制取消预约",
                f"用户：{row['display_name']}（{row['username']}）\n场馆：{row['name']}\n日期：{row['slot_date']} {row['slot_time']}\n当前状态：{STATUS_LABELS.get(row['status'], row['status'])}",
                "填写后台取消原因，例如场馆维护、异常占用、重复预约等",
            )
            if dialog.exec() != QDialog.Accepted:
                return
            reason = dialog.reason()
        ok, msg = self.model.admin_cancel_booking(booking_id, reason)
        self.show_toast(msg, ok)
        if ok:
            self.refresh_admin_bookings()
            self.refresh_admin_overview()
            self.refresh_admin_logs()

    def refresh_admin_activities(self) -> None:
        self.admin_activity_rows = self.model.admin_activities()
        self.fill_table(
            self.admin_activity_table,
            [[r["title"], r["category"], r["organizer_name"], r["start_time"], r["location"], str(r["registered_count"]), STATUS_LABELS.get(r["status"], r["status"])] for r in self.admin_activity_rows],
            6,
        )

    def admin_cancel_activity(self) -> None:
        activity_id = self.current_admin_ids.get("activity")
        if activity_id is None:
            self.show_toast("请先选择活动", False)
            return
        row = next((item for item in self.admin_activity_rows if item["id"] == activity_id), None)
        reason = ""
        if row is not None:
            dialog = ReasonDialog(
                self,
                "取消活动",
                f"活动：{row['title']}\n组织者：{row['organizer_name']}\n时间：{row['start_time']}\n报名数：{row['registered_count']}\n当前状态：{STATUS_LABELS.get(row['status'], row['status'])}",
                "填写取消原因，例如时间调整、人数不足、场地冲突等",
            )
            if dialog.exec() != QDialog.Accepted:
                return
            reason = dialog.reason()
        ok, msg = self.model.admin_cancel_activity(activity_id, reason)
        self.show_toast(msg, ok)
        if ok:
            self.refresh_admin_activities()
            self.refresh_admin_overview()
            self.refresh_admin_logs()

    def admin_show_activity_detail(self) -> None:
        activity_id = self.current_admin_ids.get("activity")
        if activity_id is None:
            self.show_toast("请先选择活动", False)
            return
        detail = self.model.get_activity(activity_id)
        if detail is None:
            self.show_toast("活动不存在", False)
            return
        dialog = DetailDialog(
            self,
            detail["title"],
            f"{detail['category']} · {detail['organizer_name']}",
            STATUS_LABELS.get(detail["status"], detail["status"]),
            detail["status"],
        )
        dialog.add_meta_grid([
            ("时间", detail["start_time"]),
            ("地点", detail["location"]),
            ("容量", str(detail["capacity"])),
            ("报名", str(detail["registered_count"])),
        ])
        dialog.add_section("活动简介", detail["summary"], 100)
        members = "\n".join(f"{m['display_name']} / {m['college']}" for m in detail["members"]) or "暂无报名成员"
        dialog.add_section("报名成员", members, 150)
        dialog.add_actions([("关闭", dialog.reject, "secondary")])
        dialog.exec()

    def admin_export_activity(self) -> None:
        activity_id = self.current_admin_ids.get("activity")
        if activity_id is None:
            self.show_toast("请先选择活动", False)
            return
        row = next((item for item in self.admin_activity_rows if item["id"] == activity_id), None)
        title = row["title"] if row else "当前活动"
        confirm = ConfirmDialog(self, "导出报名名单", f"确认导出「{title}」的报名名单？\n文件会保存到 data/exports 目录。")
        if confirm.exec() != QDialog.Accepted:
            return
        target = self.model.export_activity_csv(activity_id)
        self.show_toast(f"名单已导出：{target}" if target else "导出失败", bool(target))

    def refresh_admin_moments(self) -> None:
        self.admin_moment_rows = self.model.admin_moments()
        self.fill_table(
            self.admin_moment_table,
            [[r["category"], r["display_name"], r["content"][:38], str(r["like_count"]), str(r["comment_count"]), STATUS_LABELS.get(r["status"], r["status"]), r["created_at"]] for r in self.admin_moment_rows],
            5,
        )

    def admin_change_moment(self, status: str) -> None:
        moment_id = self.current_admin_ids.get("moment")
        if moment_id is None:
            self.show_toast("请先选择动态", False)
            return
        row = next((item for item in self.admin_moment_rows if item["id"] == moment_id), None)
        action = "恢复动态" if status == "normal" else "删除动态"
        reason = ""
        if row is not None:
            dialog = ReasonDialog(
                self,
                action,
                f"分类：{row['category']}\n发布人：{row['display_name']}\n内容：{row['content'][:120]}\n当前状态：{STATUS_LABELS.get(row['status'], row['status'])}",
                "填写审核原因，例如广告、敏感内容、误删恢复等",
            )
            if dialog.exec() != QDialog.Accepted:
                return
            reason = dialog.reason()
        ok, msg = self.model.admin_set_moment_status(moment_id, status, reason)
        self.show_toast(msg, ok)
        if ok:
            self.refresh_admin_moments()
            self.refresh_admin_overview()
            self.refresh_admin_logs()

    def admin_show_moment_detail(self) -> None:
        moment_id = self.current_admin_ids.get("moment")
        if moment_id is None:
            self.show_toast("请先选择动态", False)
            return
        detail = self.model.get_moment(moment_id)
        if detail is None:
            self.show_toast("动态不存在", False)
            return
        dialog = DetailDialog(
            self,
            detail["category"],
            f"{detail['display_name']} · {detail['created_at']}",
            STATUS_LABELS.get(detail["status"], detail["status"]),
            detail["status"],
        )
        dialog.add_meta_grid([
            ("发布人", detail["display_name"]),
            ("点赞", str(detail["like_count"])),
            ("评论", str(detail["comment_count"])),
            ("发布时间", detail["created_at"]),
        ])
        dialog.add_section("动态内容", detail["content"], 120)
        comments = "\n".join(f"[{c['created_at']}] {c['display_name']}: {c['content']}" for c in detail["comments"]) or "暂无评论"
        dialog.add_section("评论区", comments, 150)
        dialog.add_actions([("关闭", dialog.reject, "secondary")])
        dialog.exec()

    def refresh_admin_logs(self) -> None:
        rows = self.model.admin_logs()
        self.fill_table(
            self.admin_log_table,
            [[r["admin_name"], r["action"], r["target_type"], str(r["target_id"]), r["detail"], r["created_at"]] for r in rows],
        )
