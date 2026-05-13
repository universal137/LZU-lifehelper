from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
import hashlib
import shutil
import sqlite3
from pathlib import Path
import sys
from typing import Any
from uuid import uuid4


if getattr(sys, "frozen", False):
    RESOURCE_ROOT = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    APP_ROOT = Path(sys.executable).resolve().parent
else:
    RESOURCE_ROOT = Path(__file__).resolve().parent.parent
    APP_ROOT = RESOURCE_ROOT

DATA_DIR = APP_ROOT / "data"
IMAGE_DIR = DATA_DIR / "images"
DB_PATH = DATA_DIR / "lzu_lifehelper.db"


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_text() -> str:
    return date.today().isoformat()


def avatar_color(name: str) -> str:
    palette = ["#1D4ED8", "#0F766E", "#B45309", "#9333EA", "#DC2626", "#0EA5E9"]
    return palette[sum(ord(char) for char in name) % len(palette)]


def build_slot_days(days: int = 3) -> list[tuple[str, str]]:
    slot_times = ["08:00-09:00", "09:30-10:30", "14:00-15:00", "16:30-17:30", "19:00-20:00"]
    rows: list[tuple[str, str]] = []
    for offset in range(days):
        slot_date = (date.today() + timedelta(days=offset)).isoformat()
        for slot in slot_times:
            rows.append((slot_date, slot))
    return rows


@dataclass
class SessionUser:
    id: int
    username: str
    display_name: str
    role: str
    college: str
    avatar_color: str


class AppModel:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DB_PATH
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        self.current_user: SessionUser | None = None
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with self.connect() as conn:
            self._create_tables(conn)
            user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            if user_count == 0:
                self._seed_data(conn)

    def _create_tables(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                college TEXT NOT NULL,
                bio TEXT NOT NULL,
                avatar_color TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                campus TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT NOT NULL,
                image_path TEXT,
                seller_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (seller_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS product_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS venues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                campus TEXT NOT NULL,
                location TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS venue_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venue_id INTEGER NOT NULL,
                slot_date TEXT NOT NULL,
                slot_time TEXT NOT NULL,
                capacity INTEGER NOT NULL DEFAULT 1,
                UNIQUE (venue_id, slot_date, slot_time),
                FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slot_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (slot_id) REFERENCES venue_slots(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS shuttle_routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_name TEXT NOT NULL,
                from_campus TEXT NOT NULL,
                to_campus TEXT NOT NULL,
                station TEXT NOT NULL,
                departure_time TEXT NOT NULL,
                base_capacity INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS shuttle_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                ride_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (route_id) REFERENCES shuttle_routes(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                organizer_id INTEGER NOT NULL,
                location TEXT NOT NULL,
                start_time TEXT NOT NULL,
                capacity INTEGER NOT NULL,
                summary TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (organizer_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS activity_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE (activity_id, user_id),
                FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS moments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                image_path TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS moment_likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                moment_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE (moment_id, user_id),
                FOREIGN KEY (moment_id) REFERENCES moments(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS moment_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                moment_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (moment_id) REFERENCES moments(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """
        )

    def _seed_data(self, conn: sqlite3.Connection) -> None:
        users = [
            ("20230001", "李同学", hash_password("lzu123456"), "student", "信息科学与工程学院", "想把校园日常尽量收拢成一套顺手工具。"),
            ("20230025", "张同学", hash_password("lzu123456"), "student", "数学与统计学院", "课本、笔记、活动都希望在一个入口里解决。"),
            ("teacher01", "王老师", hash_password("lzu123456"), "teacher", "网络与信息化办公室", "负责系统运维和校园数字化体验。"),
            ("admin01", "管理员", hash_password("admin123456"), "admin", "信息化建设办公室", "维护活动、场馆和校车基础数据。"),
        ]
        for username, display_name, password_hash, role, college, bio in users:
            conn.execute(
                """
                INSERT INTO users (username, display_name, password_hash, role, college, bio, avatar_color, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (username, display_name, password_hash, role, college, bio, avatar_color(display_name), now_text()),
            )

        user_map = {row["username"]: row["id"] for row in conn.execute("SELECT id, username FROM users")}

        products = [
            ("高等数学教材", "书籍", "榆中校区", 25, "八成新，适合理工科大一学生，图书馆门口可面交。", "", user_map["20230025"]),
            ("二手羽毛球拍", "运动", "榆中校区", 68, "含拍套，适合社团新手练习。", "", user_map["20230001"]),
            ("机械键盘", "数码", "城关校区", 139, "红轴，带原装线，打字和写代码都很稳。", "", user_map["20230025"]),
            ("单词书合集", "书籍", "城关校区", 18, "四六级和考研词汇一起转。", "", user_map["teacher01"]),
            ("宿舍台灯", "日用", "榆中校区", 35, "三档调光，带 USB。", "", user_map["20230001"]),
            ("Python 课程笔记", "资料", "城关校区", 12, "自己整理的重点与实验踩坑。", "", user_map["20230025"]),
            ("校园卡保护套", "日用", "榆中校区", 6, "透明硬壳，全新。", "", user_map["20230001"]),
            ("电热水壶", "家居", "榆中校区", 42, "宿舍搬走前出掉，正常可用。", "", user_map["teacher01"]),
            ("图形学参考书", "书籍", "城关校区", 30, "有少量笔记，整体保存很好。", "", user_map["20230025"]),
            ("折叠自行车头盔", "运动", "榆中校区", 55, "女生尺寸，九成新。", "", user_map["20230001"]),
            ("平板支架", "数码", "城关校区", 15, "可调角度，上网课方便。", "", user_map["teacher01"]),
            ("摄影社灯光板", "器材", "榆中校区", 120, "社团闲置，附电源线。", "", user_map["admin01"]),
        ]
        conn.executemany(
            """
            INSERT INTO products (title, category, campus, price, description, image_path, seller_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [(*item, now_text()) for item in products],
        )

        product_ids = [row["id"] for row in conn.execute("SELECT id FROM products ORDER BY id")]
        message_rows = [
            (product_ids[0], user_map["20230001"], "这本教材可以在今晚面交吗？"),
            (product_ids[0], user_map["20230025"], "可以，19:30 图书馆东门。"),
            (product_ids[2], user_map["20230001"], "键盘支持试听吗？"),
            (product_ids[2], user_map["20230025"], "支持，明天下午都在工位。"),
        ]
        conn.executemany(
            """
            INSERT INTO product_messages (product_id, user_id, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            [(*item, now_text()) for item in message_rows],
        )

        venues = [
            ("羽毛球馆", "体育场馆", "榆中校区", "体育馆二层"),
            ("乒乓球馆", "体育场馆", "榆中校区", "体育馆一层"),
            ("报告厅 A201", "公共教室", "城关校区", "综合楼 A201"),
            ("创新工坊", "活动空间", "榆中校区", "大学生活动中心三层"),
        ]
        conn.executemany(
            "INSERT INTO venues (name, category, campus, location) VALUES (?, ?, ?, ?)",
            venues,
        )

        for venue_id in [row["id"] for row in conn.execute("SELECT id FROM venues")]:
            conn.executemany(
                "INSERT INTO venue_slots (venue_id, slot_date, slot_time, capacity) VALUES (?, ?, ?, 1)",
                [(venue_id, slot_date, slot_time) for slot_date, slot_time in build_slot_days(3)],
            )

        first_slot = conn.execute("SELECT id FROM venue_slots ORDER BY id LIMIT 1").fetchone()["id"]
        conn.execute(
            "INSERT INTO bookings (slot_id, user_id, status, created_at) VALUES (?, ?, 'active', ?)",
            (first_slot, user_map["20230001"], now_text()),
        )

        routes = [
            ("榆中 -> 城关 早班", "榆中校区", "城关校区", "图书馆东门", "07:10", 40),
            ("榆中 -> 城关 中午", "榆中校区", "城关校区", "体育馆南口", "12:20", 36),
            ("榆中 -> 城关 晚班", "榆中校区", "城关校区", "萃英大道西侧", "18:10", 42),
            ("城关 -> 榆中 上午", "城关校区", "榆中校区", "综合楼南口", "09:00", 34),
            ("城关 -> 榆中 下午", "城关校区", "榆中校区", "医学院北门", "15:00", 38),
            ("城关 -> 榆中 晚间", "城关校区", "榆中校区", "医学院北门", "21:00", 44),
        ]
        conn.executemany(
            """
            INSERT INTO shuttle_routes (route_name, from_campus, to_campus, station, departure_time, base_capacity)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            routes,
        )

        route_ids = [row["id"] for row in conn.execute("SELECT id FROM shuttle_routes ORDER BY id")]
        conn.execute(
            "INSERT INTO shuttle_tickets (route_id, user_id, ride_date, created_at) VALUES (?, ?, ?, ?)",
            (route_ids[0], user_map["20230001"], today_text(), now_text()),
        )

        activities = [
            ("春季志愿服务宣讲", "公益", user_map["teacher01"], "大学生活动中心 201", "2026-05-16 19:00", 80, "介绍暑期支教、社区服务与报名流程。"),
            ("篮球社友谊赛", "体育", user_map["20230025"], "西区篮球场", "2026-05-17 16:00", 30, "支持个人报名与自由组队。"),
            ("Open Source 夜谈", "学术", user_map["20230001"], "创新港 B102", "2026-05-18 19:30", 60, "分享 Git 协作、开源入门和项目实战经验。"),
            ("校园摄影采风", "文艺", user_map["teacher01"], "榆中校区中心湖", "2026-05-19 14:00", 24, "拍摄校园春景，统一后期交流。"),
            ("保研经验分享", "成长", user_map["admin01"], "综合楼 302", "2026-05-20 19:00", 120, "邀请不同学院同学做经验交流。"),
        ]
        conn.executemany(
            """
            INSERT INTO activities (title, category, organizer_id, location, start_time, capacity, summary, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [(*item, now_text()) for item in activities],
        )

        activity_ids = [row["id"] for row in conn.execute("SELECT id FROM activities ORDER BY id")]
        registrations = [
            (activity_ids[0], user_map["20230001"]),
            (activity_ids[2], user_map["20230025"]),
            (activity_ids[2], user_map["teacher01"]),
        ]
        conn.executemany(
            "INSERT INTO activity_registrations (activity_id, user_id, created_at) VALUES (?, ?, ?)",
            [(*item, now_text()) for item in registrations],
        )

        moments = [
            (user_map["teacher01"], "全部", "图书馆自习区今天新增了插座位，晚间会比较紧张。", ""),
            (user_map["20230025"], "失物招领", "在榆中校区食堂附近捡到一卡通一张，姓王，请联系领取。", ""),
            (user_map["20230001"], "吐槽问答", "请问城关校区自习室晚上几点关门？", ""),
            (user_map["teacher01"], "活动", "本周五志愿服务宣讲开始报名，欢迎感兴趣的同学参加。", ""),
            (user_map["20230025"], "全部", "二手市场刚更新了几件数码设备，价格都比较实在。", ""),
            (user_map["admin01"], "活动", "近期场馆预约规则做了同步调整，请留意时间冲突提示。", ""),
        ]
        conn.executemany(
            "INSERT INTO moments (user_id, category, content, image_path, created_at) VALUES (?, ?, ?, ?, ?)",
            [(*item, now_text()) for item in moments],
        )

        moment_ids = [row["id"] for row in conn.execute("SELECT id FROM moments ORDER BY id")]
        likes = [
            (moment_ids[0], user_map["20230001"]),
            (moment_ids[0], user_map["20230025"]),
            (moment_ids[2], user_map["teacher01"]),
            (moment_ids[3], user_map["20230001"]),
        ]
        comments = [
            (moment_ids[2], user_map["teacher01"], "一般 22:30 左右关闭，考试周会延长。"),
            (moment_ids[3], user_map["20230025"], "已经转发到班群了。"),
            (moment_ids[4], user_map["20230001"], "我刚看了，键盘那条挺不错。"),
        ]
        conn.executemany(
            "INSERT INTO moment_likes (moment_id, user_id, created_at) VALUES (?, ?, ?)",
            [(*item, now_text()) for item in likes],
        )
        conn.executemany(
            "INSERT INTO moment_comments (moment_id, user_id, content, created_at) VALUES (?, ?, ?, ?)",
            [(*item, now_text()) for item in comments],
        )

    def require_user(self) -> SessionUser:
        if self.current_user is None:
            raise RuntimeError("用户未登录")
        return self.current_user

    def register_user(
        self,
        username: str,
        display_name: str,
        password: str,
        role: str,
        college: str,
    ) -> tuple[bool, str]:
        if len(password) < 8:
            return False, "密码至少 8 位"
        with self.connect() as conn:
            exists = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
            if exists:
                return False, "用户名已存在"
            conn.execute(
                """
                INSERT INTO users (username, display_name, password_hash, role, college, bio, avatar_color, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    display_name,
                    hash_password(password),
                    role,
                    college,
                    "新注册用户，欢迎使用兰大生活助手。",
                    avatar_color(display_name),
                    now_text(),
                ),
            )
        return True, "注册成功，请返回登录"

    def authenticate(self, username: str, password: str) -> tuple[bool, str]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT id, username, display_name, role, college, avatar_color, password_hash
                FROM users WHERE username = ?
                """,
                (username.strip(),),
            ).fetchone()
        if row is None:
            return False, "账号不存在"
        if row["password_hash"] != hash_password(password):
            return False, "密码错误"
        self.current_user = SessionUser(
            id=row["id"],
            username=row["username"],
            display_name=row["display_name"],
            role=row["role"],
            college=row["college"],
            avatar_color=row["avatar_color"],
        )
        return True, "登录成功"

    def logout(self) -> None:
        self.current_user = None

    def dashboard_summary(self) -> dict[str, Any]:
        user = self.require_user()
        with self.connect() as conn:
            products_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            booking_count = conn.execute(
                "SELECT COUNT(*) FROM bookings WHERE user_id = ? AND status = 'active'",
                (user.id,),
            ).fetchone()[0]
            activity_count = conn.execute(
                """
                SELECT COUNT(*) FROM activity_registrations
                WHERE user_id = ?
                """,
                (user.id,),
            ).fetchone()[0]
            moment_count = conn.execute("SELECT COUNT(*) FROM moments").fetchone()[0]
            recent_products = conn.execute(
                """
                SELECT p.id, p.title, p.category, p.price, u.display_name AS seller_name
                FROM products p
                JOIN users u ON u.id = p.seller_id
                ORDER BY p.id DESC
                LIMIT 5
                """
            ).fetchall()
            recent_activities = conn.execute(
                """
                SELECT a.title, a.start_time, a.location
                FROM activities a
                ORDER BY a.start_time ASC
                LIMIT 5
                """
            ).fetchall()
        return {
            "stats": {
                "products": products_count,
                "bookings": booking_count,
                "activities": activity_count,
                "moments": moment_count,
            },
            "recent_products": [dict(row) for row in recent_products],
            "recent_activities": [dict(row) for row in recent_activities],
        }

    def copy_image(self, source_path: str | None) -> str | None:
        if not source_path:
            return None
        source = Path(source_path)
        if not source.exists():
            return None
        target_name = f"{uuid4().hex}{source.suffix.lower()}"
        target = IMAGE_DIR / target_name
        shutil.copy2(source, target)
        return str(target.relative_to(APP_ROOT))

    def list_products(self, keyword: str = "", category: str = "全部") -> list[dict[str, Any]]:
        conditions = []
        params: list[Any] = []
        if keyword.strip():
            conditions.append("(p.title LIKE ? OR p.description LIKE ?)")
            keyword_pattern = f"%{keyword.strip()}%"
            params.extend([keyword_pattern, keyword_pattern])
        if category not in ("", "全部"):
            conditions.append("p.category = ?")
            params.append(category)
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT p.*, u.display_name AS seller_name
                FROM products p
                JOIN users u ON u.id = p.seller_id
                {where_clause}
                ORDER BY p.id DESC
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def product_categories(self) -> list[str]:
        return ["全部", "书籍", "运动", "数码", "日用", "资料", "家居", "器材"]

    def create_product(
        self,
        title: str,
        category: str,
        campus: str,
        price: str,
        description: str,
        image_source_path: str | None,
    ) -> tuple[bool, str]:
        user = self.require_user()
        try:
            numeric_price = float(price)
        except ValueError:
            return False, "价格必须为数字"
        if numeric_price <= 0:
            return False, "价格必须大于 0"
        image_path = self.copy_image(image_source_path)
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO products (title, category, campus, price, description, image_path, seller_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (title, category, campus, numeric_price, description, image_path, user.id, now_text()),
            )
        return True, "商品发布成功"

    def get_product(self, product_id: int) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT p.*, u.display_name AS seller_name, u.college AS seller_college
                FROM products p
                JOIN users u ON u.id = p.seller_id
                WHERE p.id = ?
                """,
                (product_id,),
            ).fetchone()
            if row is None:
                return None
            messages = conn.execute(
                """
                SELECT m.content, m.created_at, u.display_name
                FROM product_messages m
                JOIN users u ON u.id = m.user_id
                WHERE m.product_id = ?
                ORDER BY m.id ASC
                """,
                (product_id,),
            ).fetchall()
        product = dict(row)
        product["messages"] = [dict(item) for item in messages]
        return product

    def add_product_message(self, product_id: int, content: str) -> tuple[bool, str]:
        user = self.require_user()
        if not content.strip():
            return False, "留言内容不能为空"
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO product_messages (product_id, user_id, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (product_id, user.id, content.strip(), now_text()),
            )
        return True, "留言已发送"

    def list_slots(self, category: str = "全部") -> list[dict[str, Any]]:
        params: list[Any] = []
        where_clause = ""
        if category not in ("", "全部"):
            where_clause = "WHERE v.category = ?"
            params.append(category)
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT
                    s.id,
                    v.name,
                    v.category,
                    v.campus,
                    v.location,
                    s.slot_date,
                    s.slot_time,
                    s.capacity - COALESCE(SUM(CASE WHEN b.status = 'active' THEN 1 ELSE 0 END), 0) AS seats_left
                FROM venue_slots s
                JOIN venues v ON v.id = s.venue_id
                LEFT JOIN bookings b ON b.slot_id = s.id
                {where_clause}
                GROUP BY s.id
                ORDER BY s.slot_date ASC, s.slot_time ASC, v.name ASC
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def venue_categories(self) -> list[str]:
        return ["全部", "体育场馆", "公共教室", "活动空间"]

    def create_booking(self, slot_id: int) -> tuple[bool, str]:
        user = self.require_user()
        conn = self.connect()
        try:
            conn.isolation_level = None
            conn.execute("BEGIN IMMEDIATE")
            slot = conn.execute(
                """
                SELECT
                    s.id, s.slot_date, s.slot_time, s.capacity,
                    v.name
                FROM venue_slots s
                JOIN venues v ON v.id = s.venue_id
                WHERE s.id = ?
                """,
                (slot_id,),
            ).fetchone()
            if slot is None:
                conn.execute("ROLLBACK")
                return False, "时段不存在"
            seats_left = conn.execute(
                """
                SELECT s.capacity - COUNT(b.id)
                FROM venue_slots s
                LEFT JOIN bookings b ON b.slot_id = s.id AND b.status = 'active'
                WHERE s.id = ?
                GROUP BY s.id
                """,
                (slot_id,),
            ).fetchone()[0]
            if seats_left <= 0:
                conn.execute("ROLLBACK")
                return False, "该时段已被预约"
            conflict = conn.execute(
                """
                SELECT 1
                FROM bookings b
                JOIN venue_slots s ON s.id = b.slot_id
                WHERE b.user_id = ? AND b.status = 'active' AND s.slot_date = ? AND s.slot_time = ?
                """,
                (user.id, slot["slot_date"], slot["slot_time"]),
            ).fetchone()
            if conflict:
                conn.execute("ROLLBACK")
                return False, "你在这个时间段已有其他预约"
            conn.execute(
                "INSERT INTO bookings (slot_id, user_id, status, created_at) VALUES (?, ?, 'active', ?)",
                (slot_id, user.id, now_text()),
            )
            conn.execute("COMMIT")
            return True, f"{slot['name']} 预约成功"
        except sqlite3.Error:
            conn.execute("ROLLBACK")
            return False, "预约失败，请稍后重试"
        finally:
            conn.close()

    def list_my_bookings(self) -> list[dict[str, Any]]:
        user = self.require_user()
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    b.id, b.status, b.created_at,
                    v.name, v.location, s.slot_date, s.slot_time
                FROM bookings b
                JOIN venue_slots s ON s.id = b.slot_id
                JOIN venues v ON v.id = s.venue_id
                WHERE b.user_id = ?
                ORDER BY s.slot_date DESC, s.slot_time DESC
                """,
                (user.id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def cancel_booking(self, booking_id: int) -> tuple[bool, str]:
        user = self.require_user()
        with self.connect() as conn:
            row = conn.execute(
                "SELECT status FROM bookings WHERE id = ? AND user_id = ?",
                (booking_id, user.id),
            ).fetchone()
            if row is None:
                return False, "预约记录不存在"
            if row["status"] != "active":
                return False, "该预约已处理"
            conn.execute(
                "UPDATE bookings SET status = 'cancelled' WHERE id = ?",
                (booking_id,),
            )
        return True, "预约已取消"

    def shuttle_campuses(self) -> list[str]:
        return ["全部", "榆中校区", "城关校区"]

    def _dynamic_seats_left(self, departure_time_text: str, base_capacity: int, taken: int) -> int:
        now = datetime.now()
        departure_clock = datetime.strptime(departure_time_text, "%H:%M").time()
        departure_datetime = datetime.combine(now.date(), departure_clock)
        if departure_datetime < now:
            departure_datetime += timedelta(days=1)
        minutes_left = max(0, int((departure_datetime - now).total_seconds() // 60))
        pressure = 0
        if minutes_left <= 20:
            pressure = 6
        elif minutes_left <= 45:
            pressure = 3
        elif minutes_left <= 90:
            pressure = 1
        return max(0, base_capacity - taken - pressure)

    def list_shuttle_routes(self, campus_filter: str = "全部") -> list[dict[str, Any]]:
        conditions = []
        params: list[Any] = []
        if campus_filter == "榆中校区":
            conditions.append("r.from_campus = ?")
            params.append("榆中校区")
        elif campus_filter == "城关校区":
            conditions.append("r.from_campus = ?")
            params.append("城关校区")
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT
                    r.*,
                    COUNT(t.id) AS booked_count
                FROM shuttle_routes r
                LEFT JOIN shuttle_tickets t ON t.route_id = r.id AND t.ride_date = ?
                {where_clause}
                GROUP BY r.id
                ORDER BY r.departure_time ASC
                """,
                [today_text(), *params],
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["seats_left"] = self._dynamic_seats_left(item["departure_time"], item["base_capacity"], item["booked_count"])
            result.append(item)
        return result

    def create_shuttle_ticket(self, route_id: int) -> tuple[bool, str]:
        user = self.require_user()
        with self.connect() as conn:
            existing = conn.execute(
                "SELECT 1 FROM shuttle_tickets WHERE route_id = ? AND user_id = ? AND ride_date = ?",
                (route_id, user.id, today_text()),
            ).fetchone()
            if existing:
                return False, "该班次今天已经订过"
            route = next((item for item in self.list_shuttle_routes("全部") if item["id"] == route_id), None)
            if route is None:
                return False, "班次不存在"
            if route["seats_left"] <= 0:
                return False, "当前班次余座不足"
            conn.execute(
                """
                INSERT INTO shuttle_tickets (route_id, user_id, ride_date, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (route_id, user.id, today_text(), now_text()),
            )
        return True, "校车票预订成功"

    def list_my_tickets(self) -> list[dict[str, Any]]:
        user = self.require_user()
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    t.id, t.ride_date, t.created_at,
                    r.route_name, r.station, r.departure_time, r.from_campus, r.to_campus
                FROM shuttle_tickets t
                JOIN shuttle_routes r ON r.id = t.route_id
                WHERE t.user_id = ?
                ORDER BY t.ride_date DESC, r.departure_time ASC
                """,
                (user.id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def activity_categories(self) -> list[str]:
        return ["全部", "公益", "体育", "学术", "文艺", "成长"]

    def list_activities(self, category: str = "全部") -> list[dict[str, Any]]:
        params: list[Any] = []
        where_clause = ""
        if category not in ("", "全部"):
            where_clause = "WHERE a.category = ?"
            params.append(category)
        user = self.require_user()
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT
                    a.*,
                    u.display_name AS organizer_name,
                    COUNT(ar.id) AS registered_count,
                    SUM(CASE WHEN ar.user_id = ? THEN 1 ELSE 0 END) AS joined
                FROM activities a
                JOIN users u ON u.id = a.organizer_id
                LEFT JOIN activity_registrations ar ON ar.activity_id = a.id
                {where_clause}
                GROUP BY a.id
                ORDER BY a.start_time ASC
                """,
                [user.id, *params],
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["seats_left"] = item["capacity"] - item["registered_count"]
            item["joined"] = bool(item["joined"])
            result.append(item)
        return result

    def create_activity(
        self,
        title: str,
        category: str,
        location: str,
        start_time: str,
        capacity: str,
        summary: str,
    ) -> tuple[bool, str]:
        user = self.require_user()
        if user.role not in {"teacher", "admin"}:
            return False, "只有教师或管理员可发布活动"
        try:
            capacity_value = int(capacity)
        except ValueError:
            return False, "人数上限必须是整数"
        if capacity_value <= 0:
            return False, "人数上限必须大于 0"
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO activities (title, category, organizer_id, location, start_time, capacity, summary, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (title, category, user.id, location, start_time, capacity_value, summary, now_text()),
            )
        return True, "活动发布成功"

    def get_activity(self, activity_id: int) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT
                    a.*,
                    u.display_name AS organizer_name,
                    COUNT(ar.id) AS registered_count
                FROM activities a
                JOIN users u ON u.id = a.organizer_id
                LEFT JOIN activity_registrations ar ON ar.activity_id = a.id
                WHERE a.id = ?
                GROUP BY a.id
                """,
                (activity_id,),
            ).fetchone()
            if row is None:
                return None
            members = conn.execute(
                """
                SELECT u.display_name, u.college
                FROM activity_registrations ar
                JOIN users u ON u.id = ar.user_id
                WHERE ar.activity_id = ?
                ORDER BY ar.id ASC
                """,
                (activity_id,),
            ).fetchall()
        result = dict(row)
        result["members"] = [dict(item) for item in members]
        result["seats_left"] = result["capacity"] - result["registered_count"]
        return result

    def register_activity(self, activity_id: int) -> tuple[bool, str]:
        user = self.require_user()
        conn = self.connect()
        try:
            conn.isolation_level = None
            conn.execute("BEGIN IMMEDIATE")
            activity = conn.execute(
                "SELECT capacity FROM activities WHERE id = ?",
                (activity_id,),
            ).fetchone()
            if activity is None:
                conn.execute("ROLLBACK")
                return False, "活动不存在"
            exists = conn.execute(
                "SELECT 1 FROM activity_registrations WHERE activity_id = ? AND user_id = ?",
                (activity_id, user.id),
            ).fetchone()
            if exists:
                conn.execute("ROLLBACK")
                return False, "你已经报名过该活动"
            count = conn.execute(
                "SELECT COUNT(*) FROM activity_registrations WHERE activity_id = ?",
                (activity_id,),
            ).fetchone()[0]
            if count >= activity["capacity"]:
                conn.execute("ROLLBACK")
                return False, "活动人数已满"
            conn.execute(
                "INSERT INTO activity_registrations (activity_id, user_id, created_at) VALUES (?, ?, ?)",
                (activity_id, user.id, now_text()),
            )
            conn.execute("COMMIT")
            return True, "报名成功"
        except sqlite3.Error:
            conn.execute("ROLLBACK")
            return False, "报名失败，请稍后再试"
        finally:
            conn.close()

    def export_activity_csv(self, activity_id: int) -> str:
        detail = self.get_activity(activity_id)
        if detail is None:
            return ""
        rows = ["姓名,学院,活动名称,活动时间,地点"]
        for member in detail["members"]:
            rows.append(f"{member['display_name']},{member['college']},{detail['title']},{detail['start_time']},{detail['location']}")
        return "\n".join(rows)

    def moment_categories(self) -> list[str]:
        return ["全部", "失物招领", "吐槽问答", "活动"]

    def list_moments(self, category: str = "全部") -> list[dict[str, Any]]:
        params: list[Any] = [self.require_user().id]
        where_clause = ""
        if category not in ("", "全部"):
            where_clause = "WHERE m.category = ?"
            params = [category, self.require_user().id]
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT
                    m.*,
                    u.display_name,
                    u.avatar_color,
                    COUNT(DISTINCT ml.id) AS like_count,
                    COUNT(DISTINCT mc.id) AS comment_count,
                    MAX(CASE WHEN ml.user_id = ? THEN 1 ELSE 0 END) AS liked
                FROM moments m
                JOIN users u ON u.id = m.user_id
                LEFT JOIN moment_likes ml ON ml.moment_id = m.id
                LEFT JOIN moment_comments mc ON mc.moment_id = m.id
                {where_clause}
                GROUP BY m.id
                ORDER BY m.id DESC
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def get_moment(self, moment_id: int) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT
                    m.*,
                    u.display_name,
                    u.avatar_color,
                    COUNT(DISTINCT ml.id) AS like_count,
                    COUNT(DISTINCT mc.id) AS comment_count
                FROM moments m
                JOIN users u ON u.id = m.user_id
                LEFT JOIN moment_likes ml ON ml.moment_id = m.id
                LEFT JOIN moment_comments mc ON mc.moment_id = m.id
                WHERE m.id = ?
                GROUP BY m.id
                """,
                (moment_id,),
            ).fetchone()
            if row is None:
                return None
            comments = conn.execute(
                """
                SELECT mc.content, mc.created_at, u.display_name
                FROM moment_comments mc
                JOIN users u ON u.id = mc.user_id
                WHERE mc.moment_id = ?
                ORDER BY mc.id ASC
                """,
                (moment_id,),
            ).fetchall()
        moment = dict(row)
        moment["comments"] = [dict(item) for item in comments]
        return moment

    def create_moment(self, category: str, content: str, image_source_path: str | None) -> tuple[bool, str]:
        user = self.require_user()
        if not content.strip():
            return False, "动态内容不能为空"
        image_path = self.copy_image(image_source_path)
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO moments (user_id, category, content, image_path, created_at) VALUES (?, ?, ?, ?, ?)",
                (user.id, category, content.strip(), image_path, now_text()),
            )
        return True, "动态已发布"

    def toggle_like(self, moment_id: int) -> tuple[bool, str]:
        user = self.require_user()
        with self.connect() as conn:
            row = conn.execute(
                "SELECT id FROM moment_likes WHERE moment_id = ? AND user_id = ?",
                (moment_id, user.id),
            ).fetchone()
            if row:
                conn.execute("DELETE FROM moment_likes WHERE id = ?", (row["id"],))
                return True, "已取消点赞"
            conn.execute(
                "INSERT INTO moment_likes (moment_id, user_id, created_at) VALUES (?, ?, ?)",
                (moment_id, user.id, now_text()),
            )
        return True, "点赞成功"

    def add_comment(self, moment_id: int, content: str) -> tuple[bool, str]:
        user = self.require_user()
        if not content.strip():
            return False, "评论不能为空"
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO moment_comments (moment_id, user_id, content, created_at) VALUES (?, ?, ?, ?)",
                (moment_id, user.id, content.strip(), now_text()),
            )
        return True, "评论已发布"

    def profile_data(self) -> dict[str, Any]:
        user = self.require_user()
        with self.connect() as conn:
            user_row = conn.execute(
                """
                SELECT username, display_name, role, college, bio, avatar_color
                FROM users WHERE id = ?
                """,
                (user.id,),
            ).fetchone()
            my_products = conn.execute(
                "SELECT COUNT(*) FROM products WHERE seller_id = ?",
                (user.id,),
            ).fetchone()[0]
            my_moments = conn.execute(
                "SELECT COUNT(*) FROM moments WHERE user_id = ?",
                (user.id,),
            ).fetchone()[0]
        return {
            "user": dict(user_row),
            "product_count": my_products,
            "moment_count": my_moments,
            "bookings": self.list_my_bookings(),
            "tickets": self.list_my_tickets(),
        }

    def update_password(self, old_password: str, new_password: str) -> tuple[bool, str]:
        user = self.require_user()
        if len(new_password) < 8:
            return False, "新密码至少 8 位"
        with self.connect() as conn:
            row = conn.execute(
                "SELECT password_hash FROM users WHERE id = ?",
                (user.id,),
            ).fetchone()
            if row is None or row["password_hash"] != hash_password(old_password):
                return False, "原密码错误"
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (hash_password(new_password), user.id),
            )
        return True, "密码修改成功"
