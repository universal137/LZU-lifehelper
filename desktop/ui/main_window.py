from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from desktop.services.store import DesktopStore


class LoginPage(QWidget):
    def __init__(self, store: DesktopStore, on_success) -> None:
        super().__init__()
        self.store = store
        self.on_success = on_success
        self._build_ui()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        left = QFrame()
        left.setObjectName("loginLeft")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(48, 48, 48, 48)
        left_layout.setSpacing(18)

        brand = QLabel("兰大生活助手")
        brand.setObjectName("brandTitle")
        sub = QLabel("参考校园服务平台、二手交易平台与社区产品的交互方式，打造更适合桌面端的多级信息架构。")
        sub.setWordWrap(True)
        sub.setObjectName("brandText")
        left_layout.addWidget(brand)
        left_layout.addWidget(sub)

        bullets = [
            "一站式服务入口，类似“今日校园”的聚合主页",
            "二手交易模块参考闲置交易类产品的信息卡片与会话感",
            "生活圈模块借鉴社区型产品的标签流与内容分层",
        ]
        for text in bullets:
            row = QLabel(f"• {text}")
            row.setObjectName("brandBullet")
            row.setWordWrap(True)
            left_layout.addWidget(row)
        left_layout.addStretch(1)

        right = QFrame()
        right.setObjectName("loginRight")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(60, 80, 60, 80)
        right_layout.setSpacing(20)
        right_layout.addStretch(1)

        card = QFrame()
        card.setObjectName("loginCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(16)

        title = QLabel("欢迎登录")
        title.setObjectName("loginTitle")
        subtitle = QLabel("使用校园账号进入桌面服务系统")
        subtitle.setObjectName("loginSubtitle")
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("账号 / 学号")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        card_layout.addWidget(self.username_input)
        card_layout.addWidget(self.password_input)

        login_button = QPushButton("登录系统")
        login_button.clicked.connect(self.submit_login)
        card_layout.addWidget(login_button)

        demo_label = QLabel("演示账号")
        demo_label.setObjectName("sectionCaption")
        card_layout.addWidget(demo_label)
        for item in self.store.list_demo_accounts():
            button = QPushButton(item["label"])
            button.setObjectName("ghostButton")
            button.clicked.connect(lambda _checked=False, data=item: self.fill_demo(data))
            card_layout.addWidget(button)

        self.tip_label = QLabel("默认学生账号可直接体验所有基础流程。")
        self.tip_label.setObjectName("loginHint")
        self.tip_label.setWordWrap(True)
        card_layout.addWidget(self.tip_label)

        right_layout.addWidget(card)
        right_layout.addStretch(1)

        root.addWidget(left, 5)
        root.addWidget(right, 4)

    def fill_demo(self, account: dict) -> None:
        self.username_input.setText(account["username"])
        self.password_input.setText(account["password"])

    def submit_login(self) -> None:
        success, message = self.store.login(self.username_input.text(), self.password_input.text())
        if not success:
            QMessageBox.warning(self, "登录失败", message)
            return
        self.on_success()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.store = DesktopStore()
        self.market_item_map: list[str] = []
        self.market_message_rows: list[dict] = []
        self.booking_slot_map: list[tuple[str, str, str]] = []
        self.booking_map: list[str] = []
        self.transit_map: list[str] = []
        self.activity_map: list[str] = []

        self.setWindowTitle("兰大生活助手")
        self.resize(1420, 900)
        self.setMinimumSize(1280, 820)
        self._apply_style()
        self._build_ui()

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background: #f5f4f2;
                color: #1d2433;
                font-family: "Microsoft YaHei UI";
                font-size: 13px;
            }
            QMainWindow {
                background: #f5f4f2;
            }
            QLabel {
                background: transparent;
            }
            QFrame#loginLeft {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #7f1d1d, stop:0.6 #9a3412, stop:1 #c2410c);
            }
            QFrame#loginRight {
                background: #f7f6f4;
            }
            QFrame#loginCard {
                background: white;
                border: 1px solid #efe6de;
                border-radius: 28px;
            }
            QFrame#sideBar {
                background: #0f172a;
                border-radius: 0;
            }
            QFrame#topBanner, QFrame#heroCard, QFrame#contentCard, QFrame#smallCard {
                background: white;
                border: 1px solid #e8e4de;
                border-radius: 20px;
            }
            QFrame#metricCard {
                border-radius: 22px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #7f1d1d, stop:1 #b45309);
            }
            QListWidget#primaryNav {
                background: transparent;
                border: none;
                outline: none;
                color: #cbd5e1;
            }
            QListWidget#primaryNav::item {
                padding: 14px 16px;
                margin: 4px 10px;
                border-radius: 14px;
            }
            QListWidget#primaryNav::item:selected {
                background: #172554;
                color: white;
            }
            QListWidget#secondaryNav {
                background: transparent;
                border: none;
                outline: none;
            }
            QListWidget#secondaryNav::item {
                padding: 10px 14px;
                margin: 0 6px 0 0;
                border-radius: 12px;
                background: #ede9e3;
                color: #475569;
            }
            QListWidget#secondaryNav::item:selected {
                background: #991b1b;
                color: white;
            }
            QPushButton {
                background: #991b1b;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 10px 16px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #7f1d1d;
            }
            QPushButton#ghostButton {
                background: #f3f1ee;
                color: #334155;
                text-align: left;
                border: 1px solid #e7dfd6;
                font-weight: 600;
            }
            QPushButton#logoutButton {
                background: #1e293b;
                border: 1px solid #334155;
            }
            QLineEdit, QComboBox, QTextEdit {
                background: #fcfbf9;
                border: 1px solid #ded7ce;
                border-radius: 12px;
                padding: 10px 12px;
            }
            QTableWidget {
                background: white;
                border: 1px solid #e8e4de;
                border-radius: 16px;
                gridline-color: #f2eee9;
            }
            QHeaderView::section {
                background: #f3eee8;
                border: none;
                border-bottom: 1px solid #e3ddd5;
                padding: 10px;
                font-weight: 700;
                color: #475569;
            }
            QGroupBox {
                background: white;
                border: 1px solid #ebe5dc;
                border-radius: 18px;
                margin-top: 12px;
                font-weight: 700;
                color: #334155;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 6px;
            }
            QLabel#brandTitle {
                color: white;
                font-size: 34px;
                font-weight: 900;
            }
            QLabel#brandText, QLabel#brandBullet {
                color: rgba(255,255,255,0.88);
                font-size: 14px;
                line-height: 1.7;
            }
            QLabel#loginTitle {
                color: #0f172a;
                font-size: 26px;
                font-weight: 900;
            }
            QLabel#loginSubtitle, QLabel#loginHint {
                color: #64748b;
                font-size: 13px;
            }
            QLabel#sectionTitle {
                color: #0f172a;
                font-size: 24px;
                font-weight: 900;
            }
            QLabel#sectionSubtitle, QLabel#sectionCaption {
                color: #64748b;
            }
            QLabel#metricTitle {
                color: rgba(255,255,255,0.8);
                font-size: 13px;
            }
            QLabel#metricValue {
                color: white;
                font-size: 30px;
                font-weight: 900;
            }
            """
        )

    def _build_ui(self) -> None:
        self.root_stack = QStackedWidget()
        self.login_page = LoginPage(self.store, self._enter_workspace)
        self.workspace = self._build_workspace()
        self.root_stack.addWidget(self.login_page)
        self.root_stack.addWidget(self.workspace)
        self.setCentralWidget(self.root_stack)
        self.root_stack.setCurrentWidget(self.login_page)

    def _build_workspace(self) -> QWidget:
        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_sidebar(), 0)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(20, 20, 20, 20)
        body_layout.setSpacing(16)

        body_layout.addWidget(self._build_top_banner())
        body_layout.addWidget(self._build_hero_section())
        body_layout.addLayout(self._build_secondary_nav())

        self.content_stack = QStackedWidget()
        body_layout.addWidget(self.content_stack, 1)

        self.dashboard_page = self._build_dashboard_page()
        self.market_page = self._build_market_page()
        self.booking_page = self._build_booking_page()
        self.transit_page = self._build_transit_page()
        self.activity_page = self._build_activity_page()
        self.moment_page = self._build_moment_page()
        self.profile_page = self._build_profile_page()

        self.content_stack.addWidget(self.dashboard_page)
        self.content_stack.addWidget(self.market_page)
        self.content_stack.addWidget(self.booking_page)
        self.content_stack.addWidget(self.transit_page)
        self.content_stack.addWidget(self.activity_page)
        self.content_stack.addWidget(self.moment_page)
        self.content_stack.addWidget(self.profile_page)

        layout.addWidget(body, 1)
        return root

    def _build_sidebar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("sideBar")
        frame.setFixedWidth(220)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(16)

        logo = QLabel("兰大生活助手")
        logo.setStyleSheet("color: white; font-size: 22px; font-weight: 900;")
        sub = QLabel("LZU CAMPUS DESKTOP")
        sub.setStyleSheet("color: #94a3b8; font-size: 11px; letter-spacing: 1px;")
        layout.addWidget(logo)
        layout.addWidget(sub)

        self.primary_nav = QListWidget()
        self.primary_nav.setObjectName("primaryNav")
        for item in ["首页概览", "二手市场", "场馆预约", "便捷出行", "社团活动", "翠英生活圈", "个人中心"]:
            QListWidgetItem(item, self.primary_nav)
        self.primary_nav.currentRowChanged.connect(self._change_primary_page)
        layout.addWidget(self.primary_nav, 1)

        self.sidebar_profile = QLabel("")
        self.sidebar_profile.setWordWrap(True)
        self.sidebar_profile.setStyleSheet("color: #cbd5e1; line-height: 1.8;")
        layout.addWidget(self.sidebar_profile)

        logout_button = QPushButton("退出登录")
        logout_button.setObjectName("logoutButton")
        logout_button.clicked.connect(self._logout)
        layout.addWidget(logout_button)
        return frame

    def _build_top_banner(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("topBanner")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 18, 20, 18)

        text_box = QVBoxLayout()
        title = QLabel("校园生活一体化工作台")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("结合今日校园式服务聚合、闲置交易式卡片浏览和社区式信息流，优化桌面端多级交互。")
        subtitle.setObjectName("sectionSubtitle")
        subtitle.setWordWrap(True)
        text_box.addWidget(title)
        text_box.addWidget(subtitle)

        right = QLabel("课程设计演示版\n支持登录、模块切换、二级导航")
        right.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        right.setStyleSheet("color: #64748b; font-size: 13px;")
        layout.addLayout(text_box, 1)
        layout.addWidget(right)
        return frame

    def _build_hero_section(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("heroCard")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        left_box = QVBoxLayout()
        self.hero_title = QLabel("")
        self.hero_title.setStyleSheet("font-size: 26px; font-weight: 900; color: #111827;")
        self.hero_desc = QLabel("")
        self.hero_desc.setWordWrap(True)
        self.hero_desc.setStyleSheet("color: #64748b; line-height: 1.7;")
        left_box.addWidget(self.hero_title)
        left_box.addWidget(self.hero_desc)

        shortcut_row = QHBoxLayout()
        self.shortcut_cards: list[QFrame] = []
        self.shortcut_labels: list[tuple[QLabel, QLabel, QLabel]] = []
        for _ in range(3):
            card = QFrame()
            card.setObjectName("smallCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 14, 14, 14)
            badge = QLabel("")
            badge.setStyleSheet("color: #991b1b; font-weight: 800;")
            title = QLabel("")
            title.setStyleSheet("font-weight: 800; font-size: 15px; color: #111827;")
            desc = QLabel("")
            desc.setWordWrap(True)
            desc.setStyleSheet("color: #64748b;")
            card_layout.addWidget(badge)
            card_layout.addWidget(title)
            card_layout.addWidget(desc)
            shortcut_row.addWidget(card)
            self.shortcut_cards.append(card)
            self.shortcut_labels.append((badge, title, desc))
        left_box.addLayout(shortcut_row)

        right_box = QHBoxLayout()
        self.metric_cards: dict[str, QLabel] = {}
        for key, title in [("marketplace_count", "在售商品"), ("booking_count", "我的预约"), ("activity_count", "活动总数")]:
            card = QFrame()
            card.setObjectName("metricCard")
            card.setMinimumWidth(170)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 16, 16, 16)
            title_label = QLabel(title)
            title_label.setObjectName("metricTitle")
            value_label = QLabel("--")
            value_label.setObjectName("metricValue")
            card_layout.addWidget(title_label)
            card_layout.addStretch(1)
            card_layout.addWidget(value_label)
            right_box.addWidget(card)
            self.metric_cards[key] = value_label

        layout.addLayout(left_box, 3)
        layout.addLayout(right_box, 2)
        return frame

    def _build_secondary_nav(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(0)
        self.secondary_nav = QListWidget()
        self.secondary_nav.setObjectName("secondaryNav")
        self.secondary_nav.setFlow(QListWidget.LeftToRight)
        self.secondary_nav.setFixedHeight(58)
        self.secondary_nav.setSpacing(6)
        self.secondary_nav.currentRowChanged.connect(self._change_secondary_view)
        layout.addWidget(self.secondary_nav)
        return layout

    def _build_dashboard_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        notice_card = QFrame()
        notice_card.setObjectName("contentCard")
        notice_layout = QVBoxLayout(notice_card)
        notice_layout.setContentsMargins(18, 18, 18, 18)
        title = QLabel("今日提醒")
        title.setStyleSheet("font-size: 18px; font-weight: 900;")
        self.notice_text = QTextEdit()
        self.notice_text.setReadOnly(True)
        notice_layout.addWidget(title)
        notice_layout.addWidget(self.notice_text)
        layout.addWidget(notice_card)
        return page

    def _build_market_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        self.market_stack = QStackedWidget()
        self.market_stack.addWidget(self._build_market_discover_view())
        self.market_stack.addWidget(self._build_market_publish_view())
        self.market_stack.addWidget(self._build_market_messages_view())
        layout.addWidget(self.market_stack)
        return page

    def _build_market_discover_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        filter_card = QFrame()
        filter_card.setObjectName("contentCard")
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(18, 18, 18, 18)
        self.market_keyword = QLineEdit()
        self.market_keyword.setPlaceholderText("搜索商品、描述或卖家")
        self.market_category = QComboBox()
        self.market_category.addItems(["全部", "书籍", "数码", "日用"])
        filter_button = QPushButton("筛选")
        filter_button.clicked.connect(self.refresh_marketplace)
        filter_layout.addWidget(self.market_keyword, 2)
        filter_layout.addWidget(self.market_category)
        filter_layout.addWidget(filter_button)
        layout.addWidget(filter_card)

        self.market_table = QTableWidget(0, 6)
        self.market_table.setHorizontalHeaderLabels(["标题", "分类", "价格", "校区", "卖家", "描述"])
        self.market_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.market_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.market_table.itemSelectionChanged.connect(self.refresh_market_item_messages)
        layout.addWidget(self.market_table, 1)

        message_card = QGroupBox("商品会话")
        message_layout = QVBoxLayout(message_card)
        self.market_messages = QTextEdit()
        self.market_messages.setReadOnly(True)
        message_layout.addWidget(self.market_messages)
        row = QHBoxLayout()
        self.market_message_input = QLineEdit()
        self.market_message_input.setPlaceholderText("输入咨询内容")
        send_button = QPushButton("发送留言")
        send_button.clicked.connect(self.send_market_message)
        row.addWidget(self.market_message_input)
        row.addWidget(send_button)
        message_layout.addLayout(row)
        layout.addWidget(message_card)
        return widget

    def _build_market_publish_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        form_card = QGroupBox("发布闲置")
        form = QFormLayout(form_card)
        self.market_title = QLineEdit()
        self.market_create_category = QComboBox()
        self.market_create_category.addItems(["书籍", "数码", "日用"])
        self.market_price = QLineEdit()
        self.market_campus = QComboBox()
        self.market_campus.addItems(["榆中校区", "城关校区"])
        self.market_desc = QTextEdit()
        self.market_desc.setFixedHeight(160)
        form.addRow("商品标题", self.market_title)
        form.addRow("商品分类", self.market_create_category)
        form.addRow("价格", self.market_price)
        form.addRow("交易校区", self.market_campus)
        form.addRow("商品描述", self.market_desc)
        publish_button = QPushButton("立即发布")
        publish_button.clicked.connect(self.create_market_item)
        form.addRow(publish_button)
        layout.addWidget(form_card)
        layout.addStretch(1)
        return widget

    def _build_market_messages_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        card = QFrame()
        card.setObjectName("contentCard")
        inner = QVBoxLayout(card)
        inner.setContentsMargins(18, 18, 18, 18)
        title = QLabel("我的沟通记录")
        title.setStyleSheet("font-size: 18px; font-weight: 900;")
        self.market_message_history = QTextEdit()
        self.market_message_history.setReadOnly(True)
        inner.addWidget(title)
        inner.addWidget(self.market_message_history)
        layout.addWidget(card)
        return widget

    def _build_booking_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.booking_stack = QStackedWidget()
        self.booking_stack.addWidget(self._build_booking_discover_view())
        self.booking_stack.addWidget(self._build_booking_record_view())
        layout.addWidget(self.booking_stack)
        return page

    def _build_booking_discover_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        card = QGroupBox("未来 3 天场馆时段")
        inner = QVBoxLayout(card)
        self.venue_table = QTableWidget(0, 5)
        self.venue_table.setHorizontalHeaderLabels(["场馆", "类型", "日期", "时段", "状态"])
        self.venue_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.venue_table.setEditTriggers(QTableWidget.NoEditTriggers)
        inner.addWidget(self.venue_table)
        button = QPushButton("预约所选时段")
        button.clicked.connect(self.create_booking)
        inner.addWidget(button)
        layout.addWidget(card)
        return widget

    def _build_booking_record_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        card = QGroupBox("我的预约记录")
        inner = QVBoxLayout(card)
        self.booking_table = QTableWidget(0, 4)
        self.booking_table.setHorizontalHeaderLabels(["场馆", "日期", "时段", "状态"])
        self.booking_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.booking_table.setEditTriggers(QTableWidget.NoEditTriggers)
        inner.addWidget(self.booking_table)
        button = QPushButton("取消所选预约")
        button.clicked.connect(self.cancel_booking)
        inner.addWidget(button)
        layout.addWidget(card)
        return widget

    def _build_transit_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.transit_stack = QStackedWidget()
        self.transit_stack.addWidget(self._build_transit_schedule_view())
        self.transit_stack.addWidget(self._build_transit_station_view())
        layout.addWidget(self.transit_stack)
        return page

    def _build_transit_schedule_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        card = QGroupBox("校车班次与订票")
        inner = QVBoxLayout(card)
        self.transit_table = QTableWidget(0, 4)
        self.transit_table.setHorizontalHeaderLabels(["线路", "发车时间", "站点", "余票"])
        self.transit_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.transit_table.setEditTriggers(QTableWidget.NoEditTriggers)
        inner.addWidget(self.transit_table)
        button = QPushButton("预订所选班次")
        button.clicked.connect(self.create_transit_booking)
        inner.addWidget(button)
        layout.addWidget(card)
        return widget

    def _build_transit_station_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        card = QFrame()
        card.setObjectName("contentCard")
        inner = QVBoxLayout(card)
        inner.setContentsMargins(18, 18, 18, 18)
        title = QLabel("共享单车与我的车票")
        title.setStyleSheet("font-size: 18px; font-weight: 900;")
        self.transit_text = QTextEdit()
        self.transit_text.setReadOnly(True)
        inner.addWidget(title)
        inner.addWidget(self.transit_text)
        layout.addWidget(card)
        return widget

    def _build_activity_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.activity_stack = QStackedWidget()
        self.activity_stack.addWidget(self._build_activity_discover_view())
        self.activity_stack.addWidget(self._build_activity_publish_view())
        layout.addWidget(self.activity_stack)
        return page

    def _build_activity_discover_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        card = QGroupBox("活动大厅")
        inner = QVBoxLayout(card)
        self.activity_table = QTableWidget(0, 6)
        self.activity_table.setHorizontalHeaderLabels(["活动", "标签", "社团", "时间", "剩余", "地点"])
        self.activity_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.activity_table.setEditTriggers(QTableWidget.NoEditTriggers)
        inner.addWidget(self.activity_table)
        row = QHBoxLayout()
        register_button = QPushButton("报名所选活动")
        register_button.clicked.connect(self.register_activity)
        export_button = QPushButton("导出报名名单")
        export_button.clicked.connect(self.export_activity)
        row.addWidget(register_button)
        row.addWidget(export_button)
        row.addStretch(1)
        inner.addLayout(row)
        layout.addWidget(card)
        return widget

    def _build_activity_publish_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        card = QGroupBox("发布社团活动")
        form = QFormLayout(card)
        self.activity_title = QLineEdit()
        self.activity_tag = QComboBox()
        self.activity_tag.addItems(["公益实践", "体育竞技", "学术讲座", "社团招新"])
        self.activity_org = QLineEdit()
        self.activity_location = QLineEdit()
        self.activity_time = QLineEdit()
        self.activity_capacity = QLineEdit()
        form.addRow("活动名称", self.activity_title)
        form.addRow("活动标签", self.activity_tag)
        form.addRow("主办社团", self.activity_org)
        form.addRow("活动地点", self.activity_location)
        form.addRow("活动时间", self.activity_time)
        form.addRow("人数上限", self.activity_capacity)
        button = QPushButton("发布活动")
        button.clicked.connect(self.create_activity)
        form.addRow(button)
        layout.addWidget(card)
        layout.addStretch(1)
        return widget

    def _build_moment_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.moment_stack = QStackedWidget()
        self.moment_stack.addWidget(self._build_moment_feed_view())
        self.moment_stack.addWidget(self._build_moment_publish_view())
        layout.addWidget(self.moment_stack)
        return page

    def _build_moment_feed_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        filter_row = QHBoxLayout()
        self.moment_filter = QComboBox()
        self.moment_filter.addItems(["全部", "校园动态", "失物招领", "互助问答"])
        filter_button = QPushButton("筛选")
        filter_button.clicked.connect(self.refresh_moments)
        filter_row.addWidget(self.moment_filter)
        filter_row.addWidget(filter_button)
        filter_row.addStretch(1)
        layout.addLayout(filter_row)

        card = QFrame()
        card.setObjectName("contentCard")
        inner = QVBoxLayout(card)
        inner.setContentsMargins(18, 18, 18, 18)
        self.moment_text = QTextEdit()
        self.moment_text.setReadOnly(True)
        inner.addWidget(self.moment_text)
        layout.addWidget(card)
        return widget

    def _build_moment_publish_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        card = QGroupBox("发布动态")
        form = QFormLayout(card)
        self.moment_author = QLineEdit()
        self.moment_tag = QComboBox()
        self.moment_tag.addItems(["校园动态", "失物招领", "互助问答"])
        self.moment_content = QTextEdit()
        self.moment_content.setFixedHeight(180)
        form.addRow("发布者", self.moment_author)
        form.addRow("内容标签", self.moment_tag)
        form.addRow("动态内容", self.moment_content)
        button = QPushButton("立即发布")
        button.clicked.connect(self.create_moment)
        form.addRow(button)
        layout.addWidget(card)
        layout.addStretch(1)
        return widget

    def _build_profile_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.profile_stack = QStackedWidget()
        self.profile_stack.addWidget(self._build_profile_overview_view())
        self.profile_stack.addWidget(self._build_profile_security_view())
        layout.addWidget(self.profile_stack)
        return page

    def _build_profile_overview_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        card = QFrame()
        card.setObjectName("contentCard")
        inner = QVBoxLayout(card)
        inner.setContentsMargins(18, 18, 18, 18)
        self.profile_text = QTextEdit()
        self.profile_text.setReadOnly(True)
        inner.addWidget(self.profile_text)
        layout.addWidget(card)
        return widget

    def _build_profile_security_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        card = QGroupBox("账户安全")
        form = QFormLayout(card)
        self.old_password = QLineEdit()
        self.old_password.setEchoMode(QLineEdit.Password)
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        form.addRow("原密码", self.old_password)
        form.addRow("新密码", self.new_password)
        form.addRow("确认密码", self.confirm_password)
        button = QPushButton("修改密码")
        button.clicked.connect(self.change_password)
        form.addRow(button)
        layout.addWidget(card)
        layout.addStretch(1)
        return widget

    def _enter_workspace(self) -> None:
        self.root_stack.setCurrentWidget(self.workspace)
        self.primary_nav.setCurrentRow(0)
        self.refresh_all()

    def _logout(self) -> None:
        self.store.logout()
        self.login_page.password_input.clear()
        self.root_stack.setCurrentWidget(self.login_page)

    def _change_primary_page(self, index: int) -> None:
        if index < 0:
            return
        self.content_stack.setCurrentIndex(index)
        secondary_map = {
            0: ["总览", "通知"],
            1: ["逛一逛", "发布闲置", "消息"],
            2: ["可预约时段", "我的预约"],
            3: ["校车订票", "单车与车票"],
            4: ["活动大厅", "发布活动"],
            5: ["动态广场", "发布动态"],
            6: ["资料概览", "账户安全"],
        }
        self.secondary_nav.blockSignals(True)
        self.secondary_nav.clear()
        for item in secondary_map.get(index, []):
            QListWidgetItem(item, self.secondary_nav)
        self.secondary_nav.blockSignals(False)
        if self.secondary_nav.count() > 0:
            self.secondary_nav.setCurrentRow(0)
        self._refresh_header_for_page(index)

    def _change_secondary_view(self, index: int) -> None:
        if index < 0:
            return
        primary_index = self.primary_nav.currentRow()
        stack_map = {
            0: None,
            1: self.market_stack,
            2: self.booking_stack,
            3: self.transit_stack,
            4: self.activity_stack,
            5: self.moment_stack,
            6: self.profile_stack,
        }
        stack = stack_map.get(primary_index)
        if stack is not None and index < stack.count():
            stack.setCurrentIndex(index)
        if primary_index == 0:
            self.notice_text.verticalScrollBar().setValue(0)

    def _refresh_header_for_page(self, index: int) -> None:
        titles = {
            0: ("首页概览", "常用服务、消息提醒和模块捷径集中展示。"),
            1: ("二手市场", "参考闲置交易产品，采用浏览、发布、消息三层结构。"),
            2: ("场馆预约", "参考校园办事入口，按“可预约时段 / 我的预约”分层。"),
            3: ("便捷出行", "把订票操作和静态出行信息分开，减少桌面页面拥挤。"),
            4: ("社团活动", "活动浏览与活动发布拆开，增强组织者和参与者场景。"),
            5: ("翠英生活圈", "社区内容和发帖入口分离，阅读与创作互不干扰。"),
            6: ("个人中心", "个人资料与账户安全独立分层，符合常见桌面软件设置模式。"),
        }
        title, desc = titles.get(index, ("兰大生活助手", ""))
        self.hero_title.setText(title)
        self.hero_desc.setText(desc)

    def refresh_all(self) -> None:
        if self.store.current_user is None:
            return
        self.refresh_dashboard()
        self.refresh_marketplace()
        self.refresh_market_message_history()
        self.refresh_bookings()
        self.refresh_transit()
        self.refresh_activities()
        self.refresh_moments()
        self.refresh_profile()

    def refresh_dashboard(self) -> None:
        data = self.store.dashboard()
        user = data["current_user"]
        self.sidebar_profile.setText(f"{user['name']}\n{user['role_label']}\n{user['college']}")
        self.metric_cards["marketplace_count"].setText(str(data["stats"]["marketplace_count"]))
        self.metric_cards["booking_count"].setText(str(data["stats"]["booking_count"]))
        self.metric_cards["activity_count"].setText(str(data["stats"]["activity_count"]))
        self.hero_title.setText("首页概览")
        self.hero_desc.setText("参考当前主流校园服务与社区产品，提供卡片式总览、多级导航和业务分层。")

        for shortcut, labels in zip(self.store.service_shortcuts(), self.shortcut_labels):
            badge, title, desc = labels
            badge.setText(shortcut["badge"])
            title.setText(shortcut["title"])
            desc.setText(shortcut["desc"])

        self.notice_text.setPlainText("\n".join([f"• {notice}" for notice in data["notices"]]))
        self.moment_author.setText(user["name"])

    def refresh_marketplace(self) -> None:
        items = self.store.list_marketplace(self.market_keyword.text(), self.market_category.currentText())
        self.market_item_map = [item["id"] for item in items]
        rows = [
            (item["title"], item["category"], f"¥{item['price']:.0f}", item["campus"], item["seller_name"], item["description"])
            for item in items
        ]
        self._fill_table(self.market_table, rows)
        self.refresh_market_item_messages()

    def refresh_market_item_messages(self) -> None:
        row = self.market_table.currentRow()
        if row < 0 or row >= len(self.market_item_map):
            self.market_messages.setPlainText("选中商品后可查看完整沟通记录。")
            return
        item_id = self.market_item_map[row]
        item = next((entry for entry in self.store.list_marketplace() if entry["id"] == item_id), None)
        if item is None or not item["messages"]:
            self.market_messages.setPlainText("暂无留言。")
            return
        lines = [f"{msg['created_at']}  {msg['user_name']}：{msg['content']}" for msg in item["messages"]]
        self.market_messages.setPlainText("\n".join(lines))

    def refresh_market_message_history(self) -> None:
        rows = self.store.list_my_market_messages()
        if not rows:
            self.market_message_history.setPlainText("当前没有与你相关的商品沟通记录。")
            return
        lines = [f"[{row['created_at']}] {row['item_title']} / {row['speaker']}：{row['content']}" for row in rows]
        self.market_message_history.setPlainText("\n".join(lines))

    def create_market_item(self) -> None:
        title = self.market_title.text().strip()
        price = self.market_price.text().strip()
        description = self.market_desc.toPlainText().strip()
        if not all([title, price, description]):
            QMessageBox.warning(self, "提示", "请完整填写商品信息")
            return
        self.store.add_marketplace_item(title, self.market_create_category.currentText(), price, description, self.market_campus.currentText())
        self.market_title.clear()
        self.market_price.clear()
        self.market_desc.clear()
        self.refresh_dashboard()
        self.refresh_marketplace()
        QMessageBox.information(self, "成功", "商品已发布")

    def send_market_message(self) -> None:
        row = self.market_table.currentRow()
        if row < 0 or row >= len(self.market_item_map):
            QMessageBox.warning(self, "提示", "请先选择商品")
            return
        content = self.market_message_input.text().strip()
        if not content:
            QMessageBox.warning(self, "提示", "请输入留言内容")
            return
        self.store.add_message(self.market_item_map[row], content)
        self.market_message_input.clear()
        self.refresh_market_item_messages()
        self.refresh_market_message_history()
        QMessageBox.information(self, "成功", "留言已发送")

    def refresh_bookings(self) -> None:
        venues = self.store.list_venues()
        rows: list[tuple[str, str, str, str, str]] = []
        self.booking_slot_map = []
        for venue in venues:
            for day in venue["schedule"]:
                for slot in day["slots"]:
                    rows.append((venue["name"], venue["type"], day["date"], slot["time"], "可预约" if slot["available"] else "已占用"))
                    self.booking_slot_map.append((venue["id"], day["date"], slot["time"]))
        self._fill_table(self.venue_table, rows)

        bookings = self.store.list_bookings()
        self.booking_map = [booking["id"] for booking in bookings]
        booking_rows = [(item["venue_name"], item["date"], item["time"], item["status"]) for item in bookings]
        self._fill_table(self.booking_table, booking_rows)

    def create_booking(self) -> None:
        row = self.venue_table.currentRow()
        if row < 0 or row >= len(self.booking_slot_map):
            QMessageBox.warning(self, "提示", "请先选择时段")
            return
        success, message = self.store.create_booking(*self.booking_slot_map[row])
        if success:
            self.refresh_dashboard()
            self.refresh_bookings()
            self.refresh_profile()
            QMessageBox.information(self, "成功", message)
        else:
            QMessageBox.warning(self, "提示", message)

    def cancel_booking(self) -> None:
        row = self.booking_table.currentRow()
        if row < 0 or row >= len(self.booking_map):
            QMessageBox.warning(self, "提示", "请先选择预约记录")
            return
        if self.store.cancel_booking(self.booking_map[row]):
            self.refresh_dashboard()
            self.refresh_bookings()
            self.refresh_profile()
            QMessageBox.information(self, "成功", "预约已取消")
        else:
            QMessageBox.warning(self, "提示", "该预约无法取消")

    def refresh_transit(self) -> None:
        snapshot = self.store.transit_snapshot()
        self.transit_map = [item["id"] for item in snapshot["schedules"]]
        rows = [(item["route"], item["departure_time"], item["station"], f"{item['seats_left']}/{item['seats_total']}") for item in snapshot["schedules"]]
        self._fill_table(self.transit_table, rows)
        lines = ["共享单车站点"]
        lines.extend(f"• {station['name']}  |  可用 {station['bikes_available']} 辆  |  {station['distance']}" for station in snapshot["bike_stations"])
        lines.append("")
        lines.append("我的车票")
        if snapshot["bookings"]:
            lines.extend(f"• {booking['route']}  {booking['departure_time']}  {booking['station']}" for booking in snapshot["bookings"])
        else:
            lines.append("• 暂无预订记录")
        self.transit_text.setPlainText("\n".join(lines))

    def create_transit_booking(self) -> None:
        row = self.transit_table.currentRow()
        if row < 0 or row >= len(self.transit_map):
            QMessageBox.warning(self, "提示", "请先选择班次")
            return
        success, message = self.store.create_transit_booking(self.transit_map[row])
        if success:
            self.refresh_transit()
            self.refresh_profile()
            QMessageBox.information(self, "成功", message)
        else:
            QMessageBox.warning(self, "提示", message)

    def refresh_activities(self) -> None:
        activities = self.store.list_activities()
        self.activity_map = [item["id"] for item in activities]
        rows = [(item["title"], item["tag"], item["organizer"], item["time"], str(item["seats_left"]), item["location"]) for item in activities]
        self._fill_table(self.activity_table, rows)

    def create_activity(self) -> None:
        values = [
            self.activity_title.text().strip(),
            self.activity_org.text().strip(),
            self.activity_location.text().strip(),
            self.activity_time.text().strip(),
            self.activity_capacity.text().strip(),
        ]
        if not all(values):
            QMessageBox.warning(self, "提示", "请完整填写活动信息")
            return
        self.store.add_activity(
            self.activity_title.text().strip(),
            self.activity_org.text().strip(),
            self.activity_location.text().strip(),
            self.activity_time.text().strip(),
            self.activity_capacity.text().strip(),
            self.activity_tag.currentText(),
        )
        self.activity_title.clear()
        self.activity_org.clear()
        self.activity_location.clear()
        self.activity_time.clear()
        self.activity_capacity.clear()
        self.refresh_dashboard()
        self.refresh_activities()
        self.refresh_profile()
        QMessageBox.information(self, "成功", "活动已发布")

    def register_activity(self) -> None:
        row = self.activity_table.currentRow()
        if row < 0 or row >= len(self.activity_map):
            QMessageBox.warning(self, "提示", "请先选择活动")
            return
        success, message = self.store.register_activity(self.activity_map[row])
        if success:
            self.refresh_activities()
            self.refresh_profile()
            QMessageBox.information(self, "成功", message)
        else:
            QMessageBox.warning(self, "提示", message)

    def export_activity(self) -> None:
        row = self.activity_table.currentRow()
        if row < 0 or row >= len(self.activity_map):
            QMessageBox.warning(self, "提示", "请先选择活动")
            return
        csv_text = self.store.export_activity(self.activity_map[row])
        if not csv_text:
            QMessageBox.warning(self, "提示", "导出失败")
            return
        target_path, _ = QFileDialog.getSaveFileName(self, "保存报名名单", str(Path.cwd() / "activity_registrations.csv"), "CSV Files (*.csv)")
        if not target_path:
            return
        Path(target_path).write_text(csv_text, encoding="utf-8-sig")
        QMessageBox.information(self, "成功", f"名单已导出到\n{target_path}")

    def refresh_moments(self) -> None:
        moments = self.store.list_moments(self.moment_filter.currentText())
        lines: list[str] = []
        for moment in moments:
            lines.append(f"[{moment['tag']}] {moment['author']} · {moment['created_at']}")
            lines.append(moment["content"])
            lines.append("")
        self.moment_text.setPlainText("\n".join(lines))

    def create_moment(self) -> None:
        content = self.moment_content.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "提示", "请输入动态内容")
            return
        self.store.add_moment(self.moment_author.text().strip(), self.moment_tag.currentText(), content)
        self.moment_content.clear()
        self.refresh_dashboard()
        self.refresh_moments()
        self.refresh_profile()
        QMessageBox.information(self, "成功", "动态已发布")

    def refresh_profile(self) -> None:
        data = self.store.user_profile()
        user = data["user"]
        lines = [
            f"姓名：{user['name']}",
            f"身份：{user['role_label']}",
            f"学院 / 单位：{user['college']}",
            f"登录账号：{user['username']}",
            "",
            "我的预约",
        ]
        if data["bookings"]:
            lines.extend(f"• {item['venue_name']}  {item['date']}  {item['time']}  {item['status']}" for item in data["bookings"])
        else:
            lines.append("• 暂无预约记录")
        lines.append("")
        lines.append("我的车票")
        if data["tickets"]:
            lines.extend(f"• {item['route']}  {item['departure_time']}  {item['station']}" for item in data["tickets"])
        else:
            lines.append("• 暂无车票记录")
        lines.append("")
        lines.append("我报名的活动")
        if data["activities"]:
            lines.extend(f"• {item['title']}  {item['time']}  {item['location']}" for item in data["activities"])
        else:
            lines.append("• 暂无报名活动")
        self.profile_text.setPlainText("\n".join(lines))

    def change_password(self) -> None:
        old_password = self.old_password.text()
        new_password = self.new_password.text()
        confirm_password = self.confirm_password.text()
        if not all([old_password, new_password, confirm_password]):
            QMessageBox.warning(self, "提示", "请填写完整密码信息")
            return
        if new_password != confirm_password:
            QMessageBox.warning(self, "提示", "两次输入的新密码不一致")
            return
        success, message = self.store.change_password(old_password, new_password)
        if success:
            self.old_password.clear()
            self.new_password.clear()
            self.confirm_password.clear()
            QMessageBox.information(self, "成功", message)
        else:
            QMessageBox.warning(self, "提示", message)

    def _fill_table(self, table: QTableWidget, rows: list[tuple[str, ...]]) -> None:
        table.clearContents()
        table.setRowCount(len(rows))
        for row_index, row_values in enumerate(rows):
            for col_index, value in enumerate(row_values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)
        table.resizeColumnsToContents()
