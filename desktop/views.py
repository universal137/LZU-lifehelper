from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
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


def shadow() -> QGraphicsDropShadowEffect:
    effect = QGraphicsDropShadowEffect()
    effect.setBlurRadius(30)
    effect.setOffset(0, 10)
    effect.setColor(QColor(120, 120, 120, 26))
    return effect


def product_pixmap(image_path: str | None, width: int, height: int) -> QPixmap:
    if image_path:
        target = APP_ROOT / image_path
        if target.exists():
            pixmap = QPixmap(str(target))
            if not pixmap.isNull():
                return pixmap.scaled(width, height, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor("#E8EEF7"))
    painter = QPainter(pixmap)
    painter.setPen(QColor("#7E91AA"))
    painter.setFont(QFont("Microsoft YaHei UI", 12, QFont.Bold))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "LZU")
    painter.end()
    return pixmap


class FadeStack(QStackedWidget):
    def __init__(self) -> None:
        super().__init__()
        self._animation: QPropertyAnimation | None = None

    def switch_to(self, index: int) -> None:
        if index == self.currentIndex():
            return
        widget = self.widget(index)
        if widget is None:
            return
        self.setCurrentIndex(index)
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(200)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.finished.connect(lambda: widget.setGraphicsEffect(None))
        animation.start()
        self._animation = animation


class Toast(QFrame):
    def __init__(self, parent: QWidget, message: str, tone: str) -> None:
        super().__init__(parent)
        self.setObjectName("toast")
        self.setWindowFlags(Qt.SubWindow | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setGraphicsEffect(shadow())
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        badge = QLabel("✓" if tone == "success" else "!")
        badge.setObjectName("toastBadge")
        title = QLabel("操作成功" if tone == "success" else "操作提示")
        title.setObjectName("toastTitle")
        body = QLabel(message)
        body.setObjectName("toastBody")
        body.setWordWrap(True)
        text = QVBoxLayout()
        text.addWidget(title)
        text.addWidget(body)
        layout.addWidget(badge)
        layout.addLayout(text)
        self.opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity)
        self.animation = QPropertyAnimation(self.opacity, b"opacity", self)
        self.animation.setDuration(200)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()
        QTimer.singleShot(2200, self.fade_out)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.adjustSize()
        self.move(self.parentWidget().width() - self.width() - 20, 20)

    def fade_out(self) -> None:
        self.animation = QPropertyAnimation(self.opacity, b"opacity", self)
        self.animation.setDuration(200)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.deleteLater)
        self.animation.start()


class ProductDialog(QDialog):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.image_path: str | None = None
        self.setWindowTitle("发布商品")
        self.resize(460, 460)
        layout = QFormLayout(self)
        self.title_input = QLineEdit()
        self.category_input = QComboBox()
        self.category_input.addItems(["书籍", "运动", "数码", "日用", "资料", "家居", "器材"])
        self.campus_input = QComboBox()
        self.campus_input.addItems(["榆中校区", "城关校区"])
        self.price_input = QLineEdit()
        self.desc_input = QTextEdit()
        self.image_label = QLabel("未选择图片")
        image_button = QPushButton("选择图片")
        image_button.clicked.connect(self.pick_image)
        submit_button = QPushButton("确认发布")
        submit_button.clicked.connect(self.accept)
        layout.addRow("标题", self.title_input)
        layout.addRow("分类", self.category_input)
        layout.addRow("校区", self.campus_input)
        layout.addRow("价格", self.price_input)
        layout.addRow("描述", self.desc_input)
        layout.addRow(self.image_label, image_button)
        layout.addRow(submit_button)

    def pick_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "选择图片", str(APP_ROOT), "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.image_path = file_path
            self.image_label.setText(Path(file_path).name)


class ActivityDialog(QDialog):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle("发布活动")
        self.resize(480, 420)
        layout = QFormLayout(self)
        self.title_input = QLineEdit()
        self.category_input = QComboBox()
        self.category_input.addItems(["公益", "体育", "学术", "文艺", "成长"])
        self.location_input = QLineEdit()
        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText("例如 2026-05-20 19:00")
        self.capacity_input = QLineEdit()
        self.summary_input = QTextEdit()
        submit_button = QPushButton("发布活动")
        submit_button.clicked.connect(self.accept)
        layout.addRow("标题", self.title_input)
        layout.addRow("分类", self.category_input)
        layout.addRow("地点", self.location_input)
        layout.addRow("时间", self.time_input)
        layout.addRow("上限", self.capacity_input)
        layout.addRow("简介", self.summary_input)
        layout.addRow(submit_button)


class MomentDialog(QDialog):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.image_path: str | None = None
        self.setWindowTitle("发布动态")
        self.resize(460, 360)
        layout = QFormLayout(self)
        self.category_input = QComboBox()
        self.category_input.addItems(["全部", "失物招领", "吐槽问答", "活动"])
        self.content_input = QTextEdit()
        self.image_label = QLabel("未选择图片")
        image_button = QPushButton("附加图片")
        image_button.clicked.connect(self.pick_image)
        submit_button = QPushButton("发布动态")
        submit_button.clicked.connect(self.accept)
        layout.addRow("分类", self.category_input)
        layout.addRow("内容", self.content_input)
        layout.addRow(self.image_label, image_button)
        layout.addRow(submit_button)

    def pick_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "选择图片", str(APP_ROOT), "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.image_path = file_path
            self.image_label.setText(Path(file_path).name)


class CommentDialog(QDialog):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle("发表评论")
        self.resize(360, 220)
        layout = QVBoxLayout(self)
        self.content_input = QTextEdit()
        submit_button = QPushButton("提交评论")
        submit_button.clicked.connect(self.accept)
        layout.addWidget(self.content_input)
        layout.addWidget(submit_button)


class AuthPage(QWidget):
    login_success = Signal()
    notify = Signal(str, str)

    def __init__(self, model: AppModel) -> None:
        super().__init__()
        self.model = model
        self.stack = FadeStack()
        self._build_ui()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        hero = QFrame()
        hero.setObjectName("authHero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(60, 60, 60, 60)
        title = QLabel("兰大生活助手")
        title.setObjectName("authTitle")
        subtitle = QLabel("Apple-style 极简桌面端，聚合交易、预约、出行、活动和生活圈。")
        subtitle.setObjectName("authSubtitle")
        subtitle.setWordWrap(True)
        hero_layout.addWidget(title)
        hero_layout.addWidget(subtitle)
        for text in [
            "透明背景与柔和阴影，消除默认 Qt 白框。",
            "SQLite 本地持久化，开箱即用，离线可运行。",
            "列表到详情页多级跳转，支持局部刷新。",
        ]:
            label = QLabel(f"• {text}")
            label.setObjectName("authBullet")
            label.setWordWrap(True)
            hero_layout.addWidget(label)
        hero_layout.addStretch(1)

        right = QWidget()
        right.setObjectName("authSurface")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(60, 50, 60, 50)
        right_layout.addStretch(1)
        right_layout.addWidget(self._build_cards())
        right_layout.addStretch(1)

        root.addWidget(hero, 5)
        root.addWidget(right, 4)

    def _build_cards(self) -> QWidget:
        wrap = QWidget()
        wrap.setObjectName("contentSurface")
        layout = QVBoxLayout(wrap)
        layout.addWidget(self.stack)
        self.stack.addWidget(self._build_login_card())
        self.stack.addWidget(self._build_register_card())
        self.stack.setCurrentIndex(0)
        return wrap

    def _build_login_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("card")
        card.setGraphicsEffect(shadow())
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("登录")
        title.setObjectName("cardTitle")
        desc = QLabel("演示账号：学生 20230001 / lzu123456，教师 teacher01 / lzu123456，管理员 admin01 / admin123456")
        desc.setObjectName("mutedText")
        desc.setWordWrap(True)
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("账号")
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("密码")
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.returnPressed.connect(self.submit_login)

        demo_row = QHBoxLayout()
        for label, username, password in [
            ("学生", "20230001", "lzu123456"),
            ("教师", "teacher01", "lzu123456"),
            ("管理员", "admin01", "admin123456"),
        ]:
            button = QPushButton(label)
            button.setObjectName("chipButton")
            button.clicked.connect(lambda _checked=False, u=username, p=password: self.fill_demo(u, p))
            demo_row.addWidget(button)

        login_button = QPushButton("进入工作台")
        login_button.clicked.connect(self.submit_login)
        register_button = QPushButton("没有账号？去注册")
        register_button.setObjectName("secondaryButton")
        register_button.clicked.connect(lambda: self.stack.switch_to(1))

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(self.login_username)
        layout.addWidget(self.login_password)
        layout.addLayout(demo_row)
        layout.addWidget(login_button)
        layout.addWidget(register_button)
        return card

    def _build_register_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("card")
        card.setGraphicsEffect(shadow())
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("注册")
        title.setObjectName("cardTitle")
        self.register_username = QLineEdit()
        self.register_username.setPlaceholderText("新账号")
        self.register_name = QLineEdit()
        self.register_name.setPlaceholderText("显示名称")
        self.register_password = QLineEdit()
        self.register_password.setPlaceholderText("密码，至少 8 位")
        self.register_password.setEchoMode(QLineEdit.Password)
        self.register_role = QComboBox()
        self.register_role.addItems(["student", "teacher"])
        self.register_college = QLineEdit()
        self.register_college.setPlaceholderText("学院 / 单位")

        register_button = QPushButton("完成注册")
        register_button.clicked.connect(self.submit_register)
        back_button = QPushButton("返回登录")
        back_button.setObjectName("secondaryButton")
        back_button.clicked.connect(lambda: self.stack.switch_to(0))

        layout.addWidget(title)
        layout.addWidget(self.register_username)
        layout.addWidget(self.register_name)
        layout.addWidget(self.register_password)
        layout.addWidget(self.register_role)
        layout.addWidget(self.register_college)
        layout.addWidget(register_button)
        layout.addWidget(back_button)
        return card

    def fill_demo(self, username: str, password: str) -> None:
        self.login_username.setText(username)
        self.login_password.setText(password)

    def submit_login(self) -> None:
        success, message = self.model.authenticate(self.login_username.text().strip(), self.login_password.text())
        self.notify.emit(message, "success" if success else "error")
        if success:
            self.login_success.emit()

    def submit_register(self) -> None:
        success, message = self.model.register_user(
            self.register_username.text().strip(),
            self.register_name.text().strip(),
            self.register_password.text(),
            self.register_role.currentText(),
            self.register_college.text().strip() or "未填写",
        )
        self.notify.emit(message, "success" if success else "error")
        if success:
            self.login_username.setText(self.register_username.text().strip())
            self.login_password.clear()
            self.register_username.clear()
            self.register_name.clear()
            self.register_password.clear()
            self.register_college.clear()
            self.stack.switch_to(0)


class MainWindow(QMainWindow):
    def __init__(self, model: AppModel) -> None:
        super().__init__()
        self.model = model
        self.current_theme = "light"
        self.current_product_id: int | None = None
        self.current_activity_id: int | None = None
        self.current_booking_id: int | None = None
        self.current_moment_id: int | None = None
        self.current_moment_filter = "全部"
        self.market_scroll_value = 0

        self.root_stack = FadeStack()
        self.page_stack = FadeStack()
        self.market_stack = FadeStack()
        self.setWindowTitle("兰大生活助手")
        self.resize(1520, 960)
        self.setMinimumSize(1280, 840)
        self._build_ui()

    def _build_ui(self) -> None:
        self.auth_page = AuthPage(self.model)
        self.auth_page.login_success.connect(self.enter_workspace)
        self.auth_page.notify.connect(self.show_toast)
        self.workspace_page = self._build_workspace_page()
        self.root_stack.addWidget(self.auth_page)
        self.root_stack.addWidget(self.workspace_page)
        self.setCentralWidget(self.root_stack)

    def _build_workspace_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("contentSurface")
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_sidebar(), 0)
        layout.addWidget(self._build_body(), 1)
        return page

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 24, 20, 24)
        layout.setSpacing(15)

        title = QLabel("兰大生活助手")
        title.setObjectName("sidebarTitle")
        subtitle = QLabel("LZU LIFE DESKTOP")
        subtitle.setObjectName("sidebarSubtitle")
        self.user_badge = QLabel("")
        self.user_badge.setObjectName("userBadge")
        self.user_badge.setWordWrap(True)

        self.nav_list = QListWidget()
        self.nav_list.setObjectName("navList")
        for text in ["首页", "二手市场", "场馆预约", "校园出行", "社团活动", "生活圈", "个人中心"]:
            QListWidgetItem(text, self.nav_list)
        self.nav_list.currentRowChanged.connect(self.change_page)

        theme_button = QPushButton("切换深浅主题")
        theme_button.setObjectName("secondaryButton")
        theme_button.clicked.connect(self.toggle_theme)
        logout_button = QPushButton("退出登录")
        logout_button.setObjectName("secondaryButton")
        logout_button.clicked.connect(self.logout)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.user_badge)
        layout.addWidget(self.nav_list, 1)
        layout.addWidget(theme_button)
        layout.addWidget(logout_button)
        return sidebar

    def _build_body(self) -> QWidget:
        body = QWidget()
        body.setObjectName("contentSurface")
        layout = QVBoxLayout(body)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(15)

        hero = QFrame()
        hero.setObjectName("heroCard")
        hero.setGraphicsEffect(shadow())
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(20, 20, 20, 20)
        title_wrap = QVBoxLayout()
        title_wrap.setSpacing(6)
        self.header_title = QLabel("首页")
        self.header_title.setObjectName("pageTitle")
        self.header_desc = QLabel("查看核心数据、最近商品和近期活动。")
        self.header_desc.setObjectName("pageSubtitle")
        title_wrap.addWidget(self.header_title)
        title_wrap.addWidget(self.header_desc)
        self.header_hint = QLabel("Apple-style / SQLite / PySide6")
        self.header_hint.setObjectName("heroHint")
        self.header_hint.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hero_layout.addLayout(title_wrap, 1)
        hero_layout.addWidget(self.header_hint)

        self.page_stack.addWidget(self._build_home_page())
        self.page_stack.addWidget(self._build_market_page())
        self.page_stack.addWidget(self._build_booking_page())
        self.page_stack.addWidget(self._build_bus_page())
        self.page_stack.addWidget(self._build_activity_page())
        self.page_stack.addWidget(self._build_moment_page())
        self.page_stack.addWidget(self._build_profile_page())

        layout.addWidget(hero)
        layout.addWidget(self.page_stack, 1)
        return body

    def _build_home_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("contentSurface")
        layout = QVBoxLayout(page)
        layout.setSpacing(15)

        top_grid = QGridLayout()
        top_grid.setSpacing(15)
        self.stat_labels: dict[str, QLabel] = {}
        stats = [("products", "在售商品数"), ("bookings", "我的预约"), ("activities", "已报活动"), ("moments", "生活圈动态")]
        for index, (key, title_text) in enumerate(stats):
            card = QFrame()
            card.setObjectName("metricCard")
            card.setGraphicsEffect(shadow())
            inner = QVBoxLayout(card)
            inner.setContentsMargins(20, 20, 20, 20)
            title = QLabel(title_text)
            title.setObjectName("metricTitle")
            value = QLabel("0")
            value.setObjectName("metricValue")
            inner.addWidget(title)
            inner.addStretch(1)
            inner.addWidget(value)
            top_grid.addWidget(card, 0, index)
            self.stat_labels[key] = value

        bottom = QHBoxLayout()
        bottom.setSpacing(15)
        self.home_products_card = self._text_card("最近上架")
        self.home_activities_card = self._text_card("近期活动")
        bottom.addWidget(self.home_products_card, 1)
        bottom.addWidget(self.home_activities_card, 1)

        layout.addLayout(top_grid)
        layout.addLayout(bottom)
        return page

    def _build_market_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("contentSurface")
        layout = QVBoxLayout(page)
        layout.setSpacing(15)

        toolbar = QFrame()
        toolbar.setObjectName("card")
        toolbar.setGraphicsEffect(shadow())
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(20, 20, 20, 20)
        self.market_keyword = QLineEdit()
        self.market_keyword.setPlaceholderText("搜索标题或描述")
        self.market_keyword.returnPressed.connect(self.refresh_market)
        self.market_category = QComboBox()
        self.market_category.addItems(self.model.product_categories())
        self.market_category.currentIndexChanged.connect(self.refresh_market)
        publish_button = QPushButton("发布商品")
        publish_button.clicked.connect(self.open_product_dialog)
        toolbar_layout.addWidget(self.market_keyword, 2)
        toolbar_layout.addWidget(self.market_category, 1)
        toolbar_layout.addWidget(publish_button)

        row = QHBoxLayout()
        row.addStretch(1)
        back_button = QPushButton("返回商品列表")
        back_button.setObjectName("secondaryButton")
        back_button.clicked.connect(self.back_to_market_grid)
        row.addWidget(back_button)

        self.market_stack.addWidget(self._build_market_grid_page())
        self.market_stack.addWidget(self._build_market_detail_page())

        layout.addWidget(toolbar)
        layout.addLayout(row)
        layout.addWidget(self.market_stack, 1)
        return page

    def _build_market_grid_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("contentSurface")
        layout = QVBoxLayout(page)
        self.market_scroll = QScrollArea()
        self.market_scroll.setWidgetResizable(True)
        self.market_scroll.setFrameShape(QScrollArea.NoFrame)
        self.market_container = QWidget()
        self.market_container.setObjectName("contentSurface")
        self.market_grid = QGridLayout(self.market_container)
        self.market_grid.setSpacing(15)
        self.market_scroll.setWidget(self.market_container)
        layout.addWidget(self.market_scroll)
        return page

    def _build_market_detail_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("contentSurface")
        layout = QHBoxLayout(page)
        layout.setSpacing(15)

        left = QFrame()
        left.setObjectName("card")
        left.setGraphicsEffect(shadow())
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(20, 20, 20, 20)
        self.product_image = QLabel()
        self.product_image.setMinimumHeight(320)
        self.product_image.setAlignment(Qt.AlignCenter)
        self.product_title = QLabel("")
        self.product_title.setObjectName("cardTitle")
        self.product_meta = QLabel("")
        self.product_meta.setObjectName("mutedText")
        self.product_meta.setWordWrap(True)
        self.product_desc = QTextEdit()
        self.product_desc.setReadOnly(True)
        left_layout.addWidget(self.product_image)
        left_layout.addWidget(self.product_title)
        left_layout.addWidget(self.product_meta)
        left_layout.addWidget(self.product_desc, 1)

        right = QFrame()
        right.setObjectName("card")
        right.setGraphicsEffect(shadow())
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(20, 20, 20, 20)
        msg_title = QLabel("留言板")
        msg_title.setObjectName("cardTitle")
        self.product_messages = QTextEdit()
        self.product_messages.setReadOnly(True)
        self.product_message_input = QTextEdit()
        self.product_message_input.setPlaceholderText("输入留言内容")
        send_button = QPushButton("发送留言")
        send_button.clicked.connect(self.send_product_message)
        right_layout.addWidget(msg_title)
        right_layout.addWidget(self.product_messages, 2)
        right_layout.addWidget(self.product_message_input, 1)
        right_layout.addWidget(send_button)

        layout.addWidget(left, 3)
        layout.addWidget(right, 2)
        return page

    def _build_booking_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("contentSurface")
        layout = QHBoxLayout(page)
        layout.setSpacing(15)

        left = QFrame()
        left.setObjectName("card")
        left.setGraphicsEffect(shadow())
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(20, 20, 20, 20)
        filter_row = QHBoxLayout()
        self.booking_category = QComboBox()
        self.booking_category.addItems(self.model.venue_categories())
        self.booking_category.currentIndexChanged.connect(self.refresh_bookings)
        filter_row.addWidget(QLabel("场馆类型"))
        filter_row.addWidget(self.booking_category)
        filter_row.addStretch(1)
        self.slot_table = self._table(["场馆", "类别", "校区", "位置", "日期", "时段", "余位"])
        self.slot_table.itemSelectionChanged.connect(self.update_slot_detail)
        book_button = QPushButton("预约当前时段")
        book_button.clicked.connect(self.create_booking)
        left_layout.addLayout(filter_row)
        left_layout.addWidget(self.slot_table, 1)
        left_layout.addWidget(book_button)

        right = QFrame()
        right.setObjectName("card")
        right.setGraphicsEffect(shadow())
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(20, 20, 20, 20)
        self.slot_detail = QTextEdit()
        self.slot_detail.setReadOnly(True)
        self.booking_table = self._table(["场馆", "位置", "日期", "时段", "状态"])
        self.booking_table.itemSelectionChanged.connect(self.capture_booking_selection)
        cancel_button = QPushButton("取消选中预约")
        cancel_button.setObjectName("secondaryButton")
        cancel_button.clicked.connect(self.cancel_booking)
        right_layout.addWidget(QLabel("时段详情"))
        right_layout.addWidget(self.slot_detail, 2)
        right_layout.addWidget(QLabel("我的预约"))
        right_layout.addWidget(self.booking_table, 2)
        right_layout.addWidget(cancel_button)

        layout.addWidget(left, 3)
        layout.addWidget(right, 2)
        return page

    def _build_bus_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("contentSurface")
        layout = QHBoxLayout(page)
        layout.setSpacing(15)

        left = QFrame()
        left.setObjectName("card")
        left.setGraphicsEffect(shadow())
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(20, 20, 20, 20)
        row = QHBoxLayout()
        self.bus_campus = QComboBox()
        self.bus_campus.addItems(self.model.shuttle_campuses())
        self.bus_campus.currentIndexChanged.connect(self.refresh_buses)
        row.addWidget(QLabel("发车校区"))
        row.addWidget(self.bus_campus)
        row.addStretch(1)
        self.bus_table = self._table(["班次", "起点", "终点", "站点", "发车时间", "实时余座"])
        ticket_button = QPushButton("预订选中班次")
        ticket_button.clicked.connect(self.create_ticket)
        left_layout.addLayout(row)
        left_layout.addWidget(self.bus_table, 1)
        left_layout.addWidget(ticket_button)

        right = self._text_card("我的校车票")
        self.ticket_text = right.findChild(QTextEdit)

        layout.addWidget(left, 3)
        layout.addWidget(right, 2)
        return page

    def _build_activity_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("contentSurface")
        layout = QHBoxLayout(page)
        layout.setSpacing(15)

        left = QFrame()
        left.setObjectName("card")
        left.setGraphicsEffect(shadow())
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(20, 20, 20, 20)
        row = QHBoxLayout()
        self.activity_category = QComboBox()
        self.activity_category.addItems(self.model.activity_categories())
        self.activity_category.currentIndexChanged.connect(self.refresh_activities)
        publish_button = QPushButton("发布活动")
        publish_button.clicked.connect(self.open_activity_dialog)
        row.addWidget(self.activity_category)
        row.addStretch(1)
        row.addWidget(publish_button)
        self.activity_table = self._table(["标题", "分类", "组织者", "时间", "地点", "余位"])
        self.activity_table.itemSelectionChanged.connect(self.open_activity_detail)
        left_layout.addLayout(row)
        left_layout.addWidget(self.activity_table, 1)

        right = QFrame()
        right.setObjectName("card")
        right.setGraphicsEffect(shadow())
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(20, 20, 20, 20)
        self.activity_detail = QTextEdit()
        self.activity_detail.setReadOnly(True)
        register_button = QPushButton("报名活动")
        register_button.clicked.connect(self.register_activity)
        export_button = QPushButton("导出报名名单")
        export_button.setObjectName("secondaryButton")
        export_button.clicked.connect(self.export_activity)
        right_layout.addWidget(QLabel("活动详情"))
        right_layout.addWidget(self.activity_detail, 1)
        right_layout.addWidget(register_button)
        right_layout.addWidget(export_button)

        layout.addWidget(left, 3)
        layout.addWidget(right, 2)
        return page

    def _build_moment_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("contentSurface")
        layout = QVBoxLayout(page)
        layout.setSpacing(15)

        row = QHBoxLayout()
        for name in self.model.moment_categories():
            button = QPushButton(name)
            button.setObjectName("chipButton")
            button.clicked.connect(lambda _checked=False, category=name: self.set_moment_filter(category))
            row.addWidget(button)
        row.addStretch(1)
        publish_button = QPushButton("发布动态")
        publish_button.clicked.connect(self.open_moment_dialog)
        row.addWidget(publish_button)

        body = QHBoxLayout()
        body.setSpacing(15)

        left = QFrame()
        left.setObjectName("card")
        left.setGraphicsEffect(shadow())
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(20, 20, 20, 20)
        self.moment_list = QListWidget()
        self.moment_list.setObjectName("momentList")
        self.moment_list.itemSelectionChanged.connect(self.open_moment_detail)
        left_layout.addWidget(QLabel("动态流"))
        left_layout.addWidget(self.moment_list)

        right = QFrame()
        right.setObjectName("card")
        right.setGraphicsEffect(shadow())
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(20, 20, 20, 20)
        self.moment_detail = QTextEdit()
        self.moment_detail.setReadOnly(True)
        actions = QHBoxLayout()
        like_button = QPushButton("点赞 / 取消点赞")
        like_button.clicked.connect(self.toggle_like)
        comment_button = QPushButton("评论")
        comment_button.setObjectName("secondaryButton")
        comment_button.clicked.connect(self.open_comment_dialog)
        actions.addWidget(like_button)
        actions.addWidget(comment_button)
        right_layout.addWidget(QLabel("详情"))
        right_layout.addWidget(self.moment_detail, 1)
        right_layout.addLayout(actions)

        body.addWidget(left, 2)
        body.addWidget(right, 3)

        layout.addLayout(row)
        layout.addLayout(body, 1)
        return page

    def _build_profile_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("contentSurface")
        layout = QHBoxLayout(page)
        layout.setSpacing(15)
        left = self._text_card("个人资料")
        self.profile_text = left.findChild(QTextEdit)

        right = QFrame()
        right.setObjectName("card")
        right.setGraphicsEffect(shadow())
        form = QFormLayout(right)
        form.setContentsMargins(20, 20, 20, 20)
        self.old_password = QLineEdit()
        self.old_password.setEchoMode(QLineEdit.Password)
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        submit_button = QPushButton("修改密码")
        submit_button.clicked.connect(self.change_password)
        form.addRow("原密码", self.old_password)
        form.addRow("新密码", self.new_password)
        form.addRow("确认密码", self.confirm_password)
        form.addRow(submit_button)

        layout.addWidget(left, 3)
        layout.addWidget(right, 2)
        return page

    def _text_card(self, title_text: str) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setGraphicsEffect(shadow())
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        title = QLabel(title_text)
        title.setObjectName("cardTitle")
        text = QTextEdit()
        text.setReadOnly(True)
        layout.addWidget(title)
        layout.addWidget(text)
        return card

    def _table(self, headers: list[str]) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)
        return table

    def enter_workspace(self) -> None:
        user = self.model.require_user()
        role_map = {"student": "学生", "teacher": "教师", "admin": "管理员"}
        self.user_badge.setText(f"{user.display_name}\n{role_map.get(user.role, user.role)} | {user.college}")
        self.root_stack.switch_to(1)
        self.nav_list.setCurrentRow(0)
        self.refresh_all()

    def refresh_all(self) -> None:
        self.refresh_home()
        self.refresh_market()
        self.refresh_bookings()
        self.refresh_buses()
        self.refresh_activities()
        self.refresh_moments()
        self.refresh_profile()

    def change_page(self, index: int) -> None:
        titles = [
            ("首页", "查看核心数据、最近商品和近期活动。"),
            ("二手市场", "支持列表到详情页跳转、图片发布、模糊搜索和留言板。"),
            ("场馆预约", "未来 3 天预约矩阵，状态变更只做局部刷新。"),
            ("校园出行", "城关与榆中班次预设，动态显示即将发车班次余座。"),
            ("社团活动", "支持活动发布、报名与名单导出。"),
            ("翠英生活圈", "顶部标签切换动态流，并支持点赞和评论。"),
            ("个人中心", "查看个人汇总信息并修改账户密码。"),
        ]
        if index < 0 or index >= len(titles):
            return
        self.header_title.setText(titles[index][0])
        self.header_desc.setText(titles[index][1])
        self.page_stack.switch_to(index)
        refresh_map = {
            0: self.refresh_home,
            1: self.refresh_market,
            2: self.refresh_bookings,
            3: self.refresh_buses,
            4: self.refresh_activities,
            5: self.refresh_moments,
            6: self.refresh_profile,
        }
        refresh_map[index]()

    def refresh_home(self) -> None:
        summary = self.model.dashboard_summary()
        for key, label in self.stat_labels.items():
            label.setText(str(summary["stats"][key]))
        self.home_products_card.findChild(QTextEdit).setPlainText(
            "\n".join(f"• {row['title']} / {row['category']} / ¥{row['price']:.0f} / {row['seller_name']}" for row in summary["recent_products"])
        )
        self.home_activities_card.findChild(QTextEdit).setPlainText(
            "\n".join(f"• {row['title']} / {row['start_time']} / {row['location']}" for row in summary["recent_activities"])
        )

    def clear_market_grid(self) -> None:
        while self.market_grid.count():
            item = self.market_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def refresh_market(self) -> None:
        self.market_rows = self.model.list_products(self.market_keyword.text(), self.market_category.currentText())
        self.clear_market_grid()
        for index, product in enumerate(self.market_rows):
            button = QPushButton()
            button.setObjectName("productCard")
            button.setMinimumHeight(360)
            button.setCursor(Qt.PointingHandCursor)
            button.setGraphicsEffect(shadow())
            content = QVBoxLayout(button)
            content.setContentsMargins(0, 0, 0, 0)
            image = QLabel()
            image.setPixmap(product_pixmap(product["image_path"], 420, 190))
            image.setFixedHeight(190)
            image.setAlignment(Qt.AlignCenter)
            text_wrap = QWidget()
            text_wrap.setObjectName("textWrap")
            text_layout = QVBoxLayout(text_wrap)
            text_layout.setContentsMargins(20, 18, 20, 20)
            title = QLabel(product["title"])
            title.setObjectName("cardTitle")
            meta = QLabel(f"{product['category']} · {product['campus']} · ¥{product['price']:.0f}")
            meta.setObjectName("mutedText")
            desc = QLabel(product["description"][:92])
            desc.setObjectName("mutedText")
            desc.setWordWrap(True)
            text_layout.addWidget(title)
            text_layout.addWidget(meta)
            text_layout.addWidget(desc)
            text_layout.addStretch(1)
            content.addWidget(image)
            content.addWidget(text_wrap)
            button.clicked.connect(lambda _checked=False, product_id=product["id"]: self.open_product_detail(product_id))
            self.market_grid.addWidget(button, index // 3, index % 3)

    def open_product_detail(self, product_id: int) -> None:
        self.market_scroll_value = self.market_scroll.verticalScrollBar().value()
        detail = self.model.get_product(product_id)
        if detail is None:
            self.show_toast("商品不存在", "error")
            return
        self.current_product_id = product_id
        self.product_image.setPixmap(product_pixmap(detail["image_path"], 620, 320))
        self.product_title.setText(detail["title"])
        self.product_meta.setText(
            f"分类：{detail['category']} · 校区：{detail['campus']} · 价格：¥{detail['price']:.2f}\n卖家：{detail['seller_name']} · 单位：{detail['seller_college']}"
        )
        self.product_desc.setPlainText(detail["description"])
        self.product_messages.setPlainText(
            "\n".join(f"[{row['created_at']}] {row['display_name']}：{row['content']}" for row in detail["messages"]) or "还没有留言，来发第一条。"
        )
        self.market_stack.switch_to(1)

    def back_to_market_grid(self) -> None:
        self.market_stack.switch_to(0)
        QTimer.singleShot(40, lambda: self.market_scroll.verticalScrollBar().setValue(self.market_scroll_value))

    def send_product_message(self) -> None:
        if self.current_product_id is None:
            self.show_toast("请先选择商品", "error")
            return
        success, message = self.model.add_product_message(self.current_product_id, self.product_message_input.toPlainText().strip())
        self.show_toast(message, "success" if success else "error")
        if success:
            self.product_message_input.clear()
            self.open_product_detail(self.current_product_id)

    def open_product_dialog(self) -> None:
        dialog = ProductDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        success, message = self.model.create_product(
            dialog.title_input.text().strip(),
            dialog.category_input.currentText(),
            dialog.campus_input.currentText(),
            dialog.price_input.text().strip(),
            dialog.desc_input.toPlainText().strip(),
            dialog.image_path,
        )
        self.show_toast(message, "success" if success else "error")
        if success:
            self.refresh_home()
            self.refresh_market()

    def fill_table(self, table: QTableWidget, rows: list[list[str]]) -> None:
        table.clearContents()
        table.setRowCount(len(rows))
        for row_index, values in enumerate(rows):
            for col_index, value in enumerate(values):
                table.setItem(row_index, col_index, QTableWidgetItem(value))
        table.resizeColumnsToContents()

    def refresh_bookings(self) -> None:
        self.slot_rows = self.model.list_slots(self.booking_category.currentText())
        self.fill_table(
            self.slot_table,
            [[row["name"], row["category"], row["campus"], row["location"], row["slot_date"], row["slot_time"], str(row["seats_left"])] for row in self.slot_rows],
        )
        if self.slot_rows:
            self.slot_table.selectRow(0)
        self.booking_rows = self.model.list_my_bookings()
        self.fill_table(
            self.booking_table,
            [[row["name"], row["location"], row["slot_date"], row["slot_time"], row["status"]] for row in self.booking_rows],
        )

    def update_slot_detail(self) -> None:
        row = self.slot_table.currentRow()
        if row < 0 or row >= len(getattr(self, "slot_rows", [])):
            return
        item = self.slot_rows[row]
        self.slot_detail.setPlainText(
            f"场馆：{item['name']}\n类别：{item['category']}\n校区：{item['campus']}\n位置：{item['location']}\n日期：{item['slot_date']}\n时段：{item['slot_time']}\n剩余名额：{item['seats_left']}"
        )

    def create_booking(self) -> None:
        row = self.slot_table.currentRow()
        if row < 0 or row >= len(getattr(self, "slot_rows", [])):
            self.show_toast("请先选择时段", "error")
            return
        success, message = self.model.create_booking(self.slot_rows[row]["id"])
        self.show_toast(message, "success" if success else "error")
        if success:
            self.refresh_home()
            self.refresh_bookings()
            self.refresh_profile()

    def capture_booking_selection(self) -> None:
        row = self.booking_table.currentRow()
        if row < 0 or row >= len(getattr(self, "booking_rows", [])):
            self.current_booking_id = None
            return
        self.current_booking_id = self.booking_rows[row]["id"]

    def cancel_booking(self) -> None:
        if self.current_booking_id is None:
            self.show_toast("请先选择预约记录", "error")
            return
        success, message = self.model.cancel_booking(self.current_booking_id)
        self.show_toast(message, "success" if success else "error")
        if success:
            self.refresh_home()
            self.refresh_bookings()
            self.refresh_profile()

    def refresh_buses(self) -> None:
        self.bus_rows = self.model.list_shuttle_routes(self.bus_campus.currentText())
        self.fill_table(
            self.bus_table,
            [[row["route_name"], row["from_campus"], row["to_campus"], row["station"], row["departure_time"], str(row["seats_left"])] for row in self.bus_rows],
        )
        self.ticket_text.setPlainText(
            "\n".join(f"• {row['ride_date']} {row['departure_time']} / {row['route_name']} / {row['station']}" for row in self.model.list_my_tickets()) or "还没有校车票。"
        )

    def create_ticket(self) -> None:
        row = self.bus_table.currentRow()
        if row < 0 or row >= len(getattr(self, "bus_rows", [])):
            self.show_toast("请先选择班次", "error")
            return
        success, message = self.model.create_shuttle_ticket(self.bus_rows[row]["id"])
        self.show_toast(message, "success" if success else "error")
        if success:
            self.refresh_buses()
            self.refresh_profile()

    def refresh_activities(self) -> None:
        self.activity_rows = self.model.list_activities(self.activity_category.currentText())
        self.fill_table(
            self.activity_table,
            [[row["title"], row["category"], row["organizer_name"], row["start_time"], row["location"], str(row["seats_left"])] for row in self.activity_rows],
        )
        if self.activity_rows:
            self.activity_table.selectRow(0)
            self.open_activity_detail()
        else:
            self.activity_detail.setPlainText("暂无活动。")

    def open_activity_detail(self) -> None:
        row = self.activity_table.currentRow()
        if row < 0 or row >= len(getattr(self, "activity_rows", [])):
            return
        self.current_activity_id = self.activity_rows[row]["id"]
        detail = self.model.get_activity(self.current_activity_id)
        if detail is None:
            return
        members = "\n".join(f"• {member['display_name']} / {member['college']}" for member in detail["members"]) or "暂无报名成员"
        self.activity_detail.setPlainText(
            f"标题：{detail['title']}\n分类：{detail['category']}\n组织者：{detail['organizer_name']}\n时间：{detail['start_time']}\n地点：{detail['location']}\n余位：{detail['seats_left']}\n\n{detail['summary']}\n\n报名成员：\n{members}"
        )

    def register_activity(self) -> None:
        if self.current_activity_id is None:
            self.show_toast("请先选择活动", "error")
            return
        success, message = self.model.register_activity(self.current_activity_id)
        self.show_toast(message, "success" if success else "error")
        if success:
            self.refresh_home()
            self.refresh_activities()
            self.refresh_profile()

    def export_activity(self) -> None:
        if self.current_activity_id is None:
            self.show_toast("请先选择活动", "error")
            return
        csv_text = self.model.export_activity_csv(self.current_activity_id)
        if not csv_text:
            self.show_toast("导出失败", "error")
            return
        target_path, _ = QFileDialog.getSaveFileName(self, "保存报名名单", str(APP_ROOT / "activity_registrations.csv"), "CSV Files (*.csv)")
        if not target_path:
            return
        Path(target_path).write_text(csv_text, encoding="utf-8-sig")
        self.show_toast("名单已导出", "success")

    def open_activity_dialog(self) -> None:
        dialog = ActivityDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        success, message = self.model.create_activity(
            dialog.title_input.text().strip(),
            dialog.category_input.currentText(),
            dialog.location_input.text().strip(),
            dialog.time_input.text().strip(),
            dialog.capacity_input.text().strip(),
            dialog.summary_input.toPlainText().strip(),
        )
        self.show_toast(message, "success" if success else "error")
        if success:
            self.refresh_home()
            self.refresh_activities()

    def set_moment_filter(self, category: str) -> None:
        self.current_moment_filter = category
        self.refresh_moments()

    def refresh_moments(self) -> None:
        self.moment_rows = self.model.list_moments(self.current_moment_filter)
        self.moment_list.clear()
        for row in self.moment_rows:
            item = QListWidgetItem(f"[{row['category']}] {row['display_name']}  {row['created_at']}\n♥ {row['like_count']}   💬 {row['comment_count']}\n{row['content'][:88]}")
            item.setData(Qt.UserRole, row["id"])
            self.moment_list.addItem(item)
        if self.moment_rows:
            self.moment_list.setCurrentRow(0)
            self.open_moment_detail()
        else:
            self.moment_detail.setPlainText("暂无动态。")

    def open_moment_detail(self) -> None:
        current = self.moment_list.currentItem()
        if current is None:
            return
        self.current_moment_id = int(current.data(Qt.UserRole))
        detail = self.model.get_moment(self.current_moment_id)
        if detail is None:
            return
        comments = "\n".join(f"[{row['created_at']}] {row['display_name']}：{row['content']}" for row in detail["comments"]) or "暂无评论"
        image_line = f"\n图片：{detail['image_path']}" if detail["image_path"] else ""
        self.moment_detail.setPlainText(
            f"作者：{detail['display_name']}\n分类：{detail['category']}\n时间：{detail['created_at']}\n点赞：{detail['like_count']}  评论：{detail['comment_count']}{image_line}\n\n{detail['content']}\n\n评论区：\n{comments}"
        )

    def open_moment_dialog(self) -> None:
        dialog = MomentDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        success, message = self.model.create_moment(dialog.category_input.currentText(), dialog.content_input.toPlainText().strip(), dialog.image_path)
        self.show_toast(message, "success" if success else "error")
        if success:
            self.refresh_home()
            self.refresh_moments()
            self.refresh_profile()

    def toggle_like(self) -> None:
        if self.current_moment_id is None:
            self.show_toast("请先选择动态", "error")
            return
        success, message = self.model.toggle_like(self.current_moment_id)
        self.show_toast(message, "success" if success else "error")
        if success:
            self.refresh_moments()
            self.open_moment_detail()

    def open_comment_dialog(self) -> None:
        if self.current_moment_id is None:
            self.show_toast("请先选择动态", "error")
            return
        dialog = CommentDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        success, message = self.model.add_comment(self.current_moment_id, dialog.content_input.toPlainText().strip())
        self.show_toast(message, "success" if success else "error")
        if success:
            self.refresh_moments()
            self.open_moment_detail()

    def refresh_profile(self) -> None:
        data = self.model.profile_data()
        user = data["user"]
        bookings = "\n".join(f"• {row['name']} / {row['slot_date']} / {row['slot_time']} / {row['status']}" for row in data["bookings"]) or "• 暂无预约"
        tickets = "\n".join(f"• {row['ride_date']} / {row['route_name']} / {row['departure_time']}" for row in data["tickets"]) or "• 暂无车票"
        self.profile_text.setPlainText(
            f"姓名：{user['display_name']}\n账号：{user['username']}\n身份：{user['role']}\n学院 / 单位：{user['college']}\n简介：{user['bio']}\n\n我发布的商品：{data['product_count']}\n我发布的动态：{data['moment_count']}\n\n预约记录：\n{bookings}\n\n车票记录：\n{tickets}"
        )

    def change_password(self) -> None:
        if self.new_password.text() != self.confirm_password.text():
            self.show_toast("两次新密码不一致", "error")
            return
        success, message = self.model.update_password(self.old_password.text(), self.new_password.text())
        self.show_toast(message, "success" if success else "error")
        if success:
            self.old_password.clear()
            self.new_password.clear()
            self.confirm_password.clear()

    def apply_theme(self) -> None:
        qss_path = RESOURCE_ROOT / "desktop" / "style.qss"
        if not qss_path.exists():
            return
        style = qss_path.read_text(encoding="utf-8")
        palettes = {
            "light": {
                "{{BG}}": "#F5F5F7",
                "{{CARD}}": "#FFFFFF",
                "{{SIDEBAR}}": "#101828",
                "{{TEXT}}": "#1D1D1F",
                "{{MUTED}}": "#86868B",
                "{{BORDER}}": "#E5E5EA",
                "{{ACCENT}}": "#0A84FF",
                "{{ACCENT_ALT}}": "#0A84FF",
                "{{ACCENT_ALT_HOVER}}": "#0077ED",
                "{{SOFT}}": "#F2F2F7",
                "{{SOFT_HOVER}}": "#EAEAEE",
                "{{CARD_HOVER}}": "#FAFAFC",
            },
            "dark": {
                "{{BG}}": "#0F1115",
                "{{CARD}}": "#171A21",
                "{{SIDEBAR}}": "#0B0D11",
                "{{TEXT}}": "#F5F5F7",
                "{{MUTED}}": "#A1A1A6",
                "{{BORDER}}": "#262A33",
                "{{ACCENT}}": "#0A84FF",
                "{{ACCENT_ALT}}": "#0A84FF",
                "{{ACCENT_ALT_HOVER}}": "#409CFF",
                "{{SOFT}}": "#1F232C",
                "{{SOFT_HOVER}}": "#2A2F38",
                "{{CARD_HOVER}}": "#1B1F27",
            },
        }
        for key, value in palettes[self.current_theme].items():
            style = style.replace(key, value)
        self.setStyleSheet(style)

    def toggle_theme(self) -> None:
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme()

    def logout(self) -> None:
        self.model.logout()
        self.root_stack.switch_to(0)

    def show_toast(self, message: str, tone: str = "success") -> None:
        toast = Toast(self, message, tone)
        toast.show()

