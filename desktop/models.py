from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import hashlib
import logging
import os
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
EXPORT_DIR = DATA_DIR / "exports"
DB_PATH = DATA_DIR / "lzu_lifehelper.db"
SCHEMA_VERSION = 3
logger = logging.getLogger("lzu_lifehelper.models")

# 增量迁移：{目标版本: [SQL语句列表]}
MIGRATIONS: dict[int, list[str]] = {
    3: [
        "CREATE INDEX IF NOT EXISTS idx_products_status_category ON products(status, category)",
        "CREATE INDEX IF NOT EXISTS idx_products_seller ON products(seller_id)",
        "CREATE INDEX IF NOT EXISTS idx_bookings_user_status ON bookings(user_id, status)",
        "CREATE INDEX IF NOT EXISTS idx_bookings_slot ON bookings(slot_id, status)",
        "CREATE INDEX IF NOT EXISTS idx_shuttle_tickets_route_date ON shuttle_tickets(route_id, ride_date)",
        "CREATE INDEX IF NOT EXISTS idx_shuttle_tickets_user ON shuttle_tickets(user_id, status)",
        "CREATE INDEX IF NOT EXISTS idx_activities_status ON activities(status)",
        "CREATE INDEX IF NOT EXISTS idx_activity_registrations_user ON activity_registrations(user_id, status)",
        "CREATE INDEX IF NOT EXISTS idx_moments_category_status ON moments(category, status)",
        "CREATE INDEX IF NOT EXISTS idx_moment_comments_moment ON moment_comments(moment_id)",
        "CREATE INDEX IF NOT EXISTS idx_moment_likes_moment ON moment_likes(moment_id)",
    ],
}


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_text() -> str:
    return date.today().isoformat()


def hash_password(password: str, salt: bytes | None = None) -> str:
    if salt is None:
        salt = os.urandom(16)
    elif isinstance(salt, str):
        salt = bytes.fromhex(salt)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"{salt.hex()}:{dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return dk.hex() == hash_hex
    except (ValueError, AttributeError):
        return False


def avatar_color(name: str) -> str:
    palette = ["#003B7C", "#00A896", "#E63946", "#495057", "#7952B3", "#0D6EFD"]
    return palette[sum(ord(ch) for ch in name) % len(palette)]


@dataclass
class SessionUser:
    id: int
    username: str
    display_name: str
    role: str
    status: str
    college: str
    avatar_color: str


class AppModel:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DB_PATH
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        self.current_user: SessionUser | None = None
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def initialize(self) -> None:
        with self.connect() as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version == 0:
            # 全新数据库，创建表和索引
            self.reset_database()
            return
        if version < SCHEMA_VERSION:
            # 增量迁移
            self._run_migrations(version)
        with self.connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            if count == 0:
                self._seed_data(conn)

    def _run_migrations(self, current_version: int) -> None:
        with self.connect() as conn:
            for target_ver in sorted(v for v in MIGRATIONS if v > current_version):
                for sql in MIGRATIONS[target_ver]:
                    conn.execute(sql)
                conn.execute(f"PRAGMA user_version = {target_ver}")

    def reset_database(self) -> None:
        if self.db_path.exists():
            try:
                self.db_path.unlink()
            except PermissionError:
                with self.connect() as conn:
                    conn.execute("PRAGMA foreign_keys = OFF")
                    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'").fetchall()
                    for row in rows:
                        conn.execute(f"DROP TABLE IF EXISTS {row['name']}")
                    conn.execute("PRAGMA foreign_keys = ON")
        with self.connect() as conn:
            self._create_tables(conn)
            self._seed_data(conn)
            conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    def _create_tables(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('student', 'teacher', 'admin')),
                status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'banned')),
                college TEXT NOT NULL,
                bio TEXT NOT NULL,
                avatar_color TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                campus TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT NOT NULL,
                image_path TEXT,
                seller_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'normal' CHECK(status IN ('normal', 'removed')),
                created_at TEXT NOT NULL,
                FOREIGN KEY (seller_id) REFERENCES users(id)
            );

            CREATE TABLE product_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE venues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                campus TEXT NOT NULL,
                location TEXT NOT NULL
            );

            CREATE TABLE venue_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venue_id INTEGER NOT NULL,
                slot_date TEXT NOT NULL,
                slot_time TEXT NOT NULL,
                capacity INTEGER NOT NULL DEFAULT 1,
                UNIQUE (venue_id, slot_date, slot_time),
                FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE
            );

            CREATE TABLE bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slot_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'cancelled', 'admin_cancelled')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (slot_id) REFERENCES venue_slots(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE shuttle_routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_name TEXT NOT NULL,
                from_campus TEXT NOT NULL,
                to_campus TEXT NOT NULL,
                station TEXT NOT NULL,
                departure_time TEXT NOT NULL,
                base_capacity INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'normal' CHECK(status IN ('normal', 'disabled'))
            );

            CREATE TABLE shuttle_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                ride_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'cancelled')),
                created_at TEXT NOT NULL,
                FOREIGN KEY (route_id) REFERENCES shuttle_routes(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                organizer_id INTEGER NOT NULL,
                location TEXT NOT NULL,
                start_time TEXT NOT NULL,
                capacity INTEGER NOT NULL,
                summary TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'normal' CHECK(status IN ('normal', 'cancelled')),
                created_at TEXT NOT NULL,
                FOREIGN KEY (organizer_id) REFERENCES users(id)
            );

            CREATE TABLE activity_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'cancelled')),
                created_at TEXT NOT NULL,
                UNIQUE (activity_id, user_id),
                FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE moments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                image_path TEXT,
                status TEXT NOT NULL DEFAULT 'normal' CHECK(status IN ('normal', 'removed')),
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE moment_likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                moment_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE (moment_id, user_id),
                FOREIGN KEY (moment_id) REFERENCES moments(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE moment_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                moment_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'normal' CHECK(status IN ('normal', 'removed')),
                created_at TEXT NOT NULL,
                FOREIGN KEY (moment_id) REFERENCES moments(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                target_type TEXT NOT NULL,
                target_id INTEGER NOT NULL,
                detail TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (admin_id) REFERENCES users(id)
            );
            """
        )
        self._create_indexes(conn)

    def _create_indexes(self, conn: sqlite3.Connection) -> None:
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_products_status_category ON products(status, category)",
            "CREATE INDEX IF NOT EXISTS idx_products_seller ON products(seller_id)",
            "CREATE INDEX IF NOT EXISTS idx_bookings_user_status ON bookings(user_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_bookings_slot ON bookings(slot_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_shuttle_tickets_route_date ON shuttle_tickets(route_id, ride_date)",
            "CREATE INDEX IF NOT EXISTS idx_shuttle_tickets_user ON shuttle_tickets(user_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_activities_status ON activities(status)",
            "CREATE INDEX IF NOT EXISTS idx_activity_registrations_user ON activity_registrations(user_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_moments_category_status ON moments(category, status)",
            "CREATE INDEX IF NOT EXISTS idx_moment_comments_moment ON moment_comments(moment_id)",
            "CREATE INDEX IF NOT EXISTS idx_moment_likes_moment ON moment_likes(moment_id)",
        ]
        for sql in indexes:
            conn.execute(sql)

    def _seed_data(self, conn: sqlite3.Connection) -> None:
        users = [
            ("20230001", "李同学", "lzu123456", "student", "信息科学与工程学院", "希望把校园日常都收进一个入口。"),
            ("20230025", "张同学", "lzu123456", "student", "数学与统计学院", "常用二手市场、活动报名和场馆预约。"),
            ("teacher01", "王老师", "lzu123456", "teacher", "网络与信息化办公室", "负责校园活动组织和信息维护。"),
            ("teacher02", "赵老师", "lzu123456", "teacher", "体育教研部", "关注场馆预约与校车出行体验。"),
            ("admin01", "系统管理员", "admin123456", "admin", "信息化建设办公室", "维护系统用户、内容和基础数据。"),
        ]
        for username, name, password, role, college, bio in users:
            conn.execute(
                """
                INSERT INTO users (username, display_name, password_hash, role, status, college, bio, avatar_color, created_at)
                VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?)
                """,
                (username, name, hash_password(password), role, college, bio, avatar_color(name), now_text()),
            )
        user_map = {row["username"]: row["id"] for row in conn.execute("SELECT id, username FROM users")}

        products = [
            ("高等数学教材", "书籍", "榆中校区", 25, "八成新，适合理工科大一学生，图书馆门口可面交。", user_map["20230025"]),
            ("二手羽毛球拍", "运动", "榆中校区", 68, "含拍套，适合社团新手练习。", user_map["20230001"]),
            ("机械键盘", "数码", "城关校区", 139, "红轴，带原装线，打字和写代码都很稳。", user_map["20230025"]),
            ("单词书合集", "资料", "城关校区", 18, "四六级和考研词汇一起转。", user_map["teacher01"]),
            ("宿舍台灯", "日用", "榆中校区", 35, "三档调光，带 USB。", user_map["20230001"]),
            ("Python 课程笔记", "资料", "城关校区", 12, "整理了重点与实验踩坑。", user_map["20230025"]),
            ("摄影社灯光板", "器材", "榆中校区", 120, "社团闲置，附电源线。", user_map["teacher02"]),
            ("平板支架", "数码", "城关校区", 15, "可调角度，上网课方便。", user_map["teacher01"]),
        ]
        conn.executemany(
            """
            INSERT INTO products (title, category, campus, price, description, image_path, seller_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, '', ?, 'normal', ?)
            """,
            [(*item, now_text()) for item in products],
        )

        product_ids = [row["id"] for row in conn.execute("SELECT id FROM products ORDER BY id")]
        messages = [
            (product_ids[0], user_map["20230001"], "这本教材可以今晚面交吗？"),
            (product_ids[0], user_map["20230025"], "可以，19:30 图书馆东门。"),
            (product_ids[2], user_map["teacher01"], "键盘支持试用吗？"),
            (product_ids[2], user_map["20230025"], "支持，明天下午都在工位。"),
        ]
        conn.executemany(
            "INSERT INTO product_messages (product_id, user_id, content, created_at) VALUES (?, ?, ?, ?)",
            [(*item, now_text()) for item in messages],
        )

        venues = [
            ("羽毛球馆", "体育场馆", "榆中校区", "体育馆二层"),
            ("乒乓球馆", "体育场馆", "榆中校区", "体育馆一层"),
            ("报告厅 A201", "公共教室", "城关校区", "综合楼 A201"),
            ("创新工坊", "活动空间", "榆中校区", "大学生活动中心三层"),
            ("研讨室 B102", "公共教室", "城关校区", "图书馆 B102"),
        ]
        conn.executemany("INSERT INTO venues (name, category, campus, location) VALUES (?, ?, ?, ?)", venues)

        slot_times = ["08:00-09:00", "09:30-10:30", "14:00-15:00", "16:30-17:30", "19:00-20:00"]
        for venue_id in [row["id"] for row in conn.execute("SELECT id FROM venues")]:
            rows = []
            for offset in range(7):
                slot_date = (date.today() + timedelta(days=offset)).isoformat()
                for slot in slot_times:
                    rows.append((venue_id, slot_date, slot, 2 if slot.startswith("19") else 1))
            conn.executemany(
                "INSERT INTO venue_slots (venue_id, slot_date, slot_time, capacity) VALUES (?, ?, ?, ?)",
                rows,
            )

        slots = [row["id"] for row in conn.execute("SELECT id FROM venue_slots ORDER BY id LIMIT 10")]
        bookings = [
            (slots[0], user_map["20230001"], "active"),
            (slots[1], user_map["20230025"], "active"),
            (slots[7], user_map["teacher01"], "cancelled"),
        ]
        conn.executemany(
            "INSERT INTO bookings (slot_id, user_id, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            [(*item, now_text(), now_text()) for item in bookings],
        )

        routes = [
            ("榆中 -> 城关 早班", "榆中校区", "城关校区", "图书馆东门", "07:10", 40),
            ("榆中 -> 城关 午班", "榆中校区", "城关校区", "体育馆南口", "12:20", 36),
            ("榆中 -> 城关 晚班", "榆中校区", "城关校区", "萃英大道西侧", "18:10", 42),
            ("城关 -> 榆中 上午", "城关校区", "榆中校区", "综合楼南口", "09:00", 34),
            ("城关 -> 榆中 下午", "城关校区", "榆中校区", "医学院北门", "15:00", 38),
            ("城关 -> 榆中 晚间", "城关校区", "榆中校区", "医学院北门", "21:00", 44),
        ]
        conn.executemany(
            """
            INSERT INTO shuttle_routes (route_name, from_campus, to_campus, station, departure_time, base_capacity, status)
            VALUES (?, ?, ?, ?, ?, ?, 'normal')
            """,
            routes,
        )

        route_ids = [row["id"] for row in conn.execute("SELECT id FROM shuttle_routes ORDER BY id")]
        conn.execute(
            "INSERT INTO shuttle_tickets (route_id, user_id, ride_date, status, created_at) VALUES (?, ?, ?, 'active', ?)",
            (route_ids[0], user_map["20230001"], today_text(), now_text()),
        )

        activities = [
            ("春季志愿服务宣讲", "公益", user_map["teacher01"], "大学生活动中心 201", "2026-06-16 19:00", 80, "介绍暑期支教、社区服务与报名流程。"),
            ("篮球社友谊赛", "体育", user_map["20230025"], "西区篮球场", "2026-06-17 16:00", 30, "支持个人报名与自由组队。"),
            ("Open Source 夜谈", "学术", user_map["20230001"], "创新港 B102", "2026-06-18 19:30", 60, "分享 Git 协作、开源入门和项目实战经验。"),
            ("校园摄影采风", "文艺", user_map["teacher02"], "榆中校区中心湖", "2026-06-19 14:00", 24, "拍摄校园夏日景观，统一后期交流。"),
            ("保研经验分享", "成长", user_map["teacher01"], "综合楼 302", "2026-06-20 19:00", 120, "邀请不同学院同学做经验交流。"),
        ]
        conn.executemany(
            """
            INSERT INTO activities (title, category, organizer_id, location, start_time, capacity, summary, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'normal', ?)
            """,
            [(*item, now_text()) for item in activities],
        )

        activity_ids = [row["id"] for row in conn.execute("SELECT id FROM activities ORDER BY id")]
        registrations = [
            (activity_ids[0], user_map["20230001"]),
            (activity_ids[2], user_map["20230025"]),
            (activity_ids[2], user_map["teacher01"]),
            (activity_ids[4], user_map["20230001"]),
        ]
        conn.executemany(
            "INSERT INTO activity_registrations (activity_id, user_id, status, created_at) VALUES (?, ?, 'active', ?)",
            [(*item, now_text()) for item in registrations],
        )

        moments = [
            (user_map["teacher01"], "校园通知", "图书馆自习区今天新增了插座位，晚上会比较紧张。"),
            (user_map["20230025"], "失物招领", "在榆中校区食堂附近捡到一卡通一张，姓王，请联系领取。"),
            (user_map["20230001"], "吐槽问答", "请问城关校区自习室晚上几点关门？"),
            (user_map["teacher02"], "活动", "本周五志愿服务宣讲开始报名，欢迎感兴趣的同学参加。"),
            (user_map["20230025"], "二手交易", "二手市场刚更新了几件数码设备，价格都比较实在。"),
            (user_map["admin01"], "校园通知", "近期场馆预约规则做了同步调整，请留意时间冲突提示。"),
        ]
        conn.executemany(
            "INSERT INTO moments (user_id, category, content, image_path, status, created_at) VALUES (?, ?, ?, '', 'normal', ?)",
            [(*item, now_text()) for item in moments],
        )
        moment_ids = [row["id"] for row in conn.execute("SELECT id FROM moments ORDER BY id")]
        conn.executemany(
            "INSERT INTO moment_likes (moment_id, user_id, created_at) VALUES (?, ?, ?)",
            [(moment_ids[0], user_map["20230001"], now_text()), (moment_ids[2], user_map["teacher01"], now_text())],
        )
        comments = [
            (moment_ids[2], user_map["teacher01"], "一般 22:30 左右关闭，考试周会延长。"),
            (moment_ids[3], user_map["20230025"], "已经转发到班群了。"),
            (moment_ids[4], user_map["20230001"], "我刚看了，键盘那条还不错。"),
        ]
        conn.executemany(
            "INSERT INTO moment_comments (moment_id, user_id, content, status, created_at) VALUES (?, ?, ?, 'normal', ?)",
            [(*item, now_text()) for item in comments],
        )

    def require_user(self) -> SessionUser:
        if self.current_user is None:
            raise RuntimeError("用户未登录")
        return self.current_user

    def require_admin(self) -> SessionUser:
        user = self.require_user()
        if user.role != "admin":
            raise PermissionError("需要管理员权限")
        return user

    def log_admin(self, action: str, target_type: str, target_id: int, detail: str) -> None:
        admin = self.require_admin()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO admin_logs (admin_id, action, target_type, target_id, detail, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (admin.id, action, target_type, target_id, detail, now_text()),
            )

    def authenticate(self, username: str, password: str) -> tuple[bool, str]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,),
            ).fetchone()
        if row is None:
            return False, "账号或密码错误"
        stored = row["password_hash"]
        # 兼容旧格式（纯SHA-256）：验证后自动升级为PBKDF2
        if ":" not in stored:
            if stored != hashlib.sha256(password.encode("utf-8")).hexdigest():
                return False, "账号或密码错误"
            new_hash = hash_password(password)
            with self.connect() as conn:
                conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, row["id"]))
        else:
            if not verify_password(password, stored):
                return False, "账号或密码错误"
        if row["status"] == "banned":
            return False, "该账号已被管理员封禁，无法登录"
        self.current_user = SessionUser(
            id=row["id"],
            username=row["username"],
            display_name=row["display_name"],
            role=row["role"],
            status=row["status"],
            college=row["college"],
            avatar_color=row["avatar_color"],
        )
        logger.info("用户登录成功: %s (%s)", username, row["role"])
        return True, "登录成功"

    def register_user(self, username: str, display_name: str, password: str, role: str, college: str) -> tuple[bool, str]:
        if role not in {"student", "teacher"}:
            return False, "只能注册学生或老师账号"
        if not username or not display_name or not password:
            return False, "账号、姓名和密码不能为空"
        if len(password) < 8:
            return False, "密码至少 8 位"
        try:
            with self.connect() as conn:
                conn.execute(
                    """
                    INSERT INTO users (username, display_name, password_hash, role, status, college, bio, avatar_color, created_at)
                    VALUES (?, ?, ?, ?, 'active', ?, '', ?, ?)
                    """,
                    (username, display_name, hash_password(password), role, college or "未填写", avatar_color(display_name), now_text()),
                )
            return True, "注册成功，请返回登录"
        except sqlite3.IntegrityError:
            return False, "账号已存在"

    def logout(self) -> None:
        self.current_user = None

    def dashboard_summary(self) -> dict[str, Any]:
        user = self.require_user()
        with self.connect() as conn:
            totals = {
                "products": conn.execute("SELECT COUNT(*) FROM products WHERE status = 'normal'").fetchone()[0],
                "bookings": conn.execute("SELECT COUNT(*) FROM bookings WHERE user_id = ? AND status = 'active'", (user.id,)).fetchone()[0],
                "tickets": conn.execute("SELECT COUNT(*) FROM shuttle_tickets WHERE user_id = ? AND status = 'active'", (user.id,)).fetchone()[0],
                "activities": conn.execute("SELECT COUNT(*) FROM activity_registrations WHERE user_id = ? AND status = 'active'", (user.id,)).fetchone()[0],
            }
            recent_products = conn.execute(
                """
                SELECT p.title, p.price, p.category, u.display_name AS seller_name
                FROM products p JOIN users u ON u.id = p.seller_id
                WHERE p.status = 'normal'
                ORDER BY p.id DESC LIMIT 4
                """
            ).fetchall()
            recent_activities = conn.execute(
                """
                SELECT title, category, start_time, location
                FROM activities
                WHERE status = 'normal'
                ORDER BY start_time ASC LIMIT 4
                """
            ).fetchall()
        return {
            "totals": totals,
            "recent_products": [dict(row) for row in recent_products],
            "recent_activities": [dict(row) for row in recent_activities],
        }

    # 图片文件魔数签名
    _IMAGE_SIGNATURES = {
        b"\x89PNG\r\n\x1a\n": ".png",
        b"\xff\xd8\xff": ".jpg",
        b"GIF87a": ".gif",
        b"GIF89a": ".gif",
        b"RIFF": ".webp",  # WEBP 文件头是 RIFF....WEBP
    }
    _MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

    def copy_image(self, image_source_path: str | None) -> str:
        if not image_source_path:
            return ""
        source = Path(image_source_path)
        if not source.exists():
            return ""
        # 大小校验
        if source.stat().st_size > self._MAX_IMAGE_SIZE:
            return ""
        # 读取文件头校验魔数
        with open(source, "rb") as f:
            header = f.read(16)
        valid_ext = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
        suffix = source.suffix.lower()
        if suffix not in valid_ext:
            return ""
        # 魔数校验（如果能匹配到则用实际类型）
        for sig, real_ext in self._IMAGE_SIGNATURES.items():
            if header.startswith(sig):
                suffix = real_ext
                break
        target = IMAGE_DIR / f"{uuid4().hex}{suffix}"
        shutil.copy2(source, target)
        return str(target.relative_to(APP_ROOT)).replace("\\", "/")

    def product_categories(self) -> list[str]:
        return ["全部", "书籍", "运动", "数码", "日用", "资料", "器材"]

    def list_products(self, keyword: str = "", category: str = "全部", include_removed: bool = False) -> list[dict[str, Any]]:
        conditions = []
        params: list[Any] = []
        if not include_removed:
            conditions.append("p.status = 'normal'")
        if keyword:
            conditions.append("(p.title LIKE ? OR p.description LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if category and category != "全部":
            conditions.append("p.category = ?")
            params.append(category)
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT p.*, u.display_name AS seller_name, u.college AS seller_college
                FROM products p
                JOIN users u ON u.id = p.seller_id
                {where_clause}
                ORDER BY p.id DESC
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def create_product(self, title: str, category: str, campus: str, price: str, description: str, image_path: str | None) -> tuple[bool, str]:
        user = self.require_user()
        if not title or not description:
            return False, "商品标题和描述不能为空"
        if len(title) > 50:
            return False, "商品标题不能超过50个字符"
        if len(description) > 2000:
            return False, "商品描述不能超过2000个字符"
        try:
            price_value = float(price)
        except ValueError:
            return False, "价格必须是数字"
        if price_value <= 0:
            return False, "价格必须大于0"
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO products (title, category, campus, price, description, image_path, seller_id, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'normal', ?)
                """,
                (title, category, campus, price_value, description, self.copy_image(image_path), user.id, now_text()),
            )
        logger.info("商品发布: %s by user %d", title, user.id)
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
                SELECT pm.content, pm.created_at, u.display_name
                FROM product_messages pm
                JOIN users u ON u.id = pm.user_id
                WHERE pm.product_id = ?
                ORDER BY pm.id ASC
                """,
                (product_id,),
            ).fetchall()
        result = dict(row)
        result["messages"] = [dict(item) for item in messages]
        return result

    def add_product_message(self, product_id: int, content: str) -> tuple[bool, str]:
        user = self.require_user()
        if not content.strip():
            return False, "留言不能为空"
        with self.connect() as conn:
            exists = conn.execute("SELECT 1 FROM products WHERE id = ? AND status = 'normal'", (product_id,)).fetchone()
            if not exists:
                return False, "商品不存在或已下架"
            conn.execute(
                "INSERT INTO product_messages (product_id, user_id, content, created_at) VALUES (?, ?, ?, ?)",
                (product_id, user.id, content.strip(), now_text()),
            )
        return True, "留言成功"

    def venue_categories(self) -> list[str]:
        return ["全部", "体育场馆", "公共教室", "活动空间"]

    def list_slots(self, category: str = "全部") -> list[dict[str, Any]]:
        params: list[Any] = []
        where = ["s.slot_date >= ?"]
        params.append(today_text())
        if category and category != "全部":
            where.append("v.category = ?")
            params.append(category)
        where_clause = "WHERE " + " AND ".join(where)
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT
                    s.id, s.slot_date, s.slot_time, s.capacity,
                    v.name, v.category, v.campus, v.location,
                    COUNT(b.id) AS booked_count
                FROM venue_slots s
                JOIN venues v ON v.id = s.venue_id
                LEFT JOIN bookings b ON b.slot_id = s.id AND b.status = 'active'
                {where_clause}
                GROUP BY s.id
                ORDER BY s.slot_date ASC, s.slot_time ASC, v.name ASC
                LIMIT 80
                """,
                params,
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["seats_left"] = item["capacity"] - item["booked_count"]
            result.append(item)
        return result

    def create_booking(self, slot_id: int) -> tuple[bool, str]:
        user = self.require_user()
        conn = self.connect()
        try:
            conn.isolation_level = None
            conn.execute("BEGIN IMMEDIATE")
            slot = conn.execute(
                "SELECT slot_date, slot_time, capacity FROM venue_slots WHERE id = ?",
                (slot_id,),
            ).fetchone()
            if slot is None:
                conn.execute("ROLLBACK")
                return False, "时段不存在"
            count = conn.execute(
                "SELECT COUNT(*) FROM bookings WHERE slot_id = ? AND status = 'active'",
                (slot_id,),
            ).fetchone()[0]
            if count >= slot["capacity"]:
                conn.execute("ROLLBACK")
                return False, "该时段已约满"
            conflict = conn.execute(
                """
                SELECT 1
                FROM bookings b JOIN venue_slots s ON s.id = b.slot_id
                WHERE b.user_id = ? AND b.status = 'active' AND s.slot_date = ? AND s.slot_time = ?
                """,
                (user.id, slot["slot_date"], slot["slot_time"]),
            ).fetchone()
            if conflict:
                conn.execute("ROLLBACK")
                return False, "你在该时间段已有其他预约"
            conn.execute(
                "INSERT INTO bookings (slot_id, user_id, status, created_at, updated_at) VALUES (?, ?, 'active', ?, ?)",
                (slot_id, user.id, now_text(), now_text()),
            )
            conn.execute("COMMIT")
            logger.info("场馆预约: slot_id=%d by user %d", slot_id, user.id)
            return True, "预约成功"
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
                SELECT b.id, b.status, b.created_at, v.name, v.location, s.slot_date, s.slot_time
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
            row = conn.execute("SELECT status FROM bookings WHERE id = ? AND user_id = ?", (booking_id, user.id)).fetchone()
            if row is None:
                return False, "预约记录不存在"
            if row["status"] != "active":
                return False, "该预约已处理"
            conn.execute("UPDATE bookings SET status = 'cancelled', updated_at = ? WHERE id = ?", (now_text(), booking_id))
        return True, "预约已取消"

    def list_shuttle_routes(self, campus_filter: str = "全部") -> list[dict[str, Any]]:
        conditions = ["r.status = 'normal'"]
        params: list[Any] = []
        if campus_filter and campus_filter != "全部":
            conditions.append("r.from_campus = ?")
            params.append(campus_filter)
        where_clause = "WHERE " + " AND ".join(conditions)
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT r.*, COUNT(t.id) AS booked_count
                FROM shuttle_routes r
                LEFT JOIN shuttle_tickets t ON t.route_id = r.id AND t.ride_date = ? AND t.status = 'active'
                {where_clause}
                GROUP BY r.id
                ORDER BY r.departure_time ASC
                """,
                [today_text(), *params],
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["seats_left"] = max(0, item["base_capacity"] - item["booked_count"])
            result.append(item)
        return result

    def create_shuttle_ticket(self, route_id: int) -> tuple[bool, str]:
        user = self.require_user()
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            exists = conn.execute(
                "SELECT 1 FROM shuttle_tickets WHERE route_id = ? AND user_id = ? AND ride_date = ? AND status = 'active'",
                (route_id, user.id, today_text()),
            ).fetchone()
            if exists:
                conn.execute("ROLLBACK")
                return False, "该班次今天已订过"
            route = conn.execute(
                "SELECT id, seats_left FROM shuttle_routes WHERE id = ?", (route_id,)
            ).fetchone()
            if route is None:
                conn.execute("ROLLBACK")
                return False, "班次不存在"
            if route["seats_left"] <= 0:
                conn.execute("ROLLBACK")
                return False, "当前班次余座不足"
            conn.execute(
                "INSERT INTO shuttle_tickets (route_id, user_id, ride_date, status, created_at) VALUES (?, ?, ?, 'active', ?)",
                (route_id, user.id, today_text(), now_text()),
            )
            conn.execute("COMMIT")
        logger.info("校车购票: route_id=%d by user %d", route_id, user.id)
        return True, "校车票预订成功"

    def list_my_tickets(self) -> list[dict[str, Any]]:
        user = self.require_user()
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT t.id, t.ride_date, t.status, t.created_at,
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

    def list_activities(self, category: str = "全部", include_cancelled: bool = False) -> list[dict[str, Any]]:
        params: list[Any] = [self.require_user().id]
        conditions = []
        if not include_cancelled:
            conditions.append("a.status = 'normal'")
        if category and category != "全部":
            conditions.append("a.category = ?")
            params.append(category)
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT a.*, u.display_name AS organizer_name,
                       COUNT(ar.id) AS registered_count,
                       MAX(CASE WHEN ar.user_id = ? AND ar.status = 'active' THEN 1 ELSE 0 END) AS joined
                FROM activities a
                JOIN users u ON u.id = a.organizer_id
                LEFT JOIN activity_registrations ar ON ar.activity_id = a.id AND ar.status = 'active'
                {where_clause}
                GROUP BY a.id
                ORDER BY a.start_time ASC
                """,
                params,
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["seats_left"] = item["capacity"] - item["registered_count"]
            item["joined"] = bool(item["joined"])
            result.append(item)
        return result

    def create_activity(self, title: str, category: str, location: str, start_time: str, capacity: str, summary: str) -> tuple[bool, str]:
        user = self.require_user()
        if user.role not in {"teacher", "admin"}:
            return False, "只有老师或管理员可以发布活动"
        if not title or not location or not start_time:
            return False, "活动标题、地点和时间不能为空"
        if len(title) > 50:
            return False, "活动标题不能超过50个字符"
        if len(location) > 100:
            return False, "地点不能超过100个字符"
        if len(summary) > 2000:
            return False, "活动简介不能超过2000个字符"
        from datetime import datetime
        try:
            datetime.strptime(start_time.strip(), "%Y-%m-%d %H:%M")
        except ValueError:
            return False, "时间格式不正确，请使用 YYYY-MM-DD HH:MM 格式"
        try:
            capacity_value = int(capacity)
        except ValueError:
            return False, "人数上限必须是整数"
        if capacity_value <= 0:
            return False, "人数上限必须大于 0"
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO activities (title, category, organizer_id, location, start_time, capacity, summary, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'normal', ?)
                """,
                (title, category, user.id, location, start_time, capacity_value, summary, now_text()),
            )
        return True, "活动发布成功"

    def get_activity(self, activity_id: int) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT a.*, u.display_name AS organizer_name,
                       COUNT(ar.id) AS registered_count
                FROM activities a
                JOIN users u ON u.id = a.organizer_id
                LEFT JOIN activity_registrations ar ON ar.activity_id = a.id AND ar.status = 'active'
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
                WHERE ar.activity_id = ? AND ar.status = 'active'
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
            activity = conn.execute("SELECT capacity, status FROM activities WHERE id = ?", (activity_id,)).fetchone()
            if activity is None or activity["status"] != "normal":
                conn.execute("ROLLBACK")
                return False, "活动不存在或已取消"
            exists = conn.execute(
                "SELECT 1 FROM activity_registrations WHERE activity_id = ? AND user_id = ? AND status = 'active'",
                (activity_id, user.id),
            ).fetchone()
            if exists:
                conn.execute("ROLLBACK")
                return False, "你已经报名过该活动"
            count = conn.execute(
                "SELECT COUNT(*) FROM activity_registrations WHERE activity_id = ? AND status = 'active'",
                (activity_id,),
            ).fetchone()[0]
            if count >= activity["capacity"]:
                conn.execute("ROLLBACK")
                return False, "活动人数已满"
            old = conn.execute(
                "SELECT id FROM activity_registrations WHERE activity_id = ? AND user_id = ?",
                (activity_id, user.id),
            ).fetchone()
            if old:
                conn.execute("UPDATE activity_registrations SET status = 'active', created_at = ? WHERE id = ?", (now_text(), old["id"]))
            else:
                conn.execute(
                    "INSERT INTO activity_registrations (activity_id, user_id, status, created_at) VALUES (?, ?, 'active', ?)",
                    (activity_id, user.id, now_text()),
                )
            conn.execute("COMMIT")
            return True, "报名成功"
        except sqlite3.Error:
            conn.execute("ROLLBACK")
            return False, "报名失败，请稍后再试"
        finally:
            conn.close()

    def export_activity_csv(self, activity_id: int) -> Path | None:
        import csv
        detail = self.get_activity(activity_id)
        if detail is None:
            return None
        target = EXPORT_DIR / f"activity_{activity_id}_registrations.csv"
        with open(target, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["姓名", "学院", "活动名称", "活动时间", "地点"])
            for member in detail["members"]:
                writer.writerow([member["display_name"], member["college"], detail["title"], detail["start_time"], detail["location"]])
        return target

    def moment_categories(self) -> list[str]:
        return ["全部", "校园通知", "失物招领", "吐槽问答", "活动", "二手交易"]

    def list_moments(self, category: str = "全部", include_removed: bool = False) -> list[dict[str, Any]]:
        user_id = self.require_user().id
        params: list[Any] = [user_id]
        conditions = []
        if not include_removed:
            conditions.append("m.status = 'normal'")
        if category and category != "全部":
            conditions.append("m.category = ?")
            params.append(category)
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT m.*, u.display_name, u.avatar_color,
                       COUNT(DISTINCT ml.id) AS like_count,
                       COUNT(DISTINCT mc.id) AS comment_count,
                       MAX(CASE WHEN ml.user_id = ? THEN 1 ELSE 0 END) AS liked
                FROM moments m
                JOIN users u ON u.id = m.user_id
                LEFT JOIN moment_likes ml ON ml.moment_id = m.id
                LEFT JOIN moment_comments mc ON mc.moment_id = m.id AND mc.status = 'normal'
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
                SELECT m.*, u.display_name, u.avatar_color,
                       COUNT(DISTINCT ml.id) AS like_count,
                       COUNT(DISTINCT mc.id) AS comment_count
                FROM moments m
                JOIN users u ON u.id = m.user_id
                LEFT JOIN moment_likes ml ON ml.moment_id = m.id
                LEFT JOIN moment_comments mc ON mc.moment_id = m.id AND mc.status = 'normal'
                WHERE m.id = ?
                GROUP BY m.id
                """,
                (moment_id,),
            ).fetchone()
            if row is None:
                return None
            comments = conn.execute(
                """
                SELECT mc.id, mc.content, mc.created_at, mc.status, u.display_name
                FROM moment_comments mc
                JOIN users u ON u.id = mc.user_id
                WHERE mc.moment_id = ? AND mc.status = 'normal'
                ORDER BY mc.id ASC
                """,
                (moment_id,),
            ).fetchall()
        result = dict(row)
        result["comments"] = [dict(item) for item in comments]
        return result

    def create_moment(self, category: str, content: str, image_path: str | None) -> tuple[bool, str]:
        user = self.require_user()
        if not content.strip():
            return False, "动态内容不能为空"
        if len(content) > 2000:
            return False, "动态内容不能超过2000个字符"
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO moments (user_id, category, content, image_path, status, created_at) VALUES (?, ?, ?, ?, 'normal', ?)",
                (user.id, category, content.strip(), self.copy_image(image_path), now_text()),
            )
        return True, "动态已发布"

    def toggle_like(self, moment_id: int) -> tuple[bool, str]:
        user = self.require_user()
        with self.connect() as conn:
            row = conn.execute("SELECT id FROM moment_likes WHERE moment_id = ? AND user_id = ?", (moment_id, user.id)).fetchone()
            if row:
                conn.execute("DELETE FROM moment_likes WHERE id = ?", (row["id"],))
                return True, "已取消点赞"
            conn.execute("INSERT INTO moment_likes (moment_id, user_id, created_at) VALUES (?, ?, ?)", (moment_id, user.id, now_text()))
        return True, "点赞成功"

    def add_comment(self, moment_id: int, content: str) -> tuple[bool, str]:
        user = self.require_user()
        if not content.strip():
            return False, "评论不能为空"
        if len(content) > 500:
            return False, "评论不能超过500个字符"
        with self.connect() as conn:
            exists = conn.execute("SELECT 1 FROM moments WHERE id = ? AND status = 'normal'", (moment_id,)).fetchone()
            if not exists:
                return False, "动态不存在或已删除"
            conn.execute(
                "INSERT INTO moment_comments (moment_id, user_id, content, status, created_at) VALUES (?, ?, ?, 'normal', ?)",
                (moment_id, user.id, content.strip(), now_text()),
            )
        return True, "评论已发布"

    def profile_data(self) -> dict[str, Any]:
        user = self.require_user()
        with self.connect() as conn:
            user_row = conn.execute(
                "SELECT username, display_name, role, status, college, bio, avatar_color, created_at FROM users WHERE id = ?",
                (user.id,),
            ).fetchone()
            product_count = conn.execute("SELECT COUNT(*) FROM products WHERE seller_id = ? AND status = 'normal'", (user.id,)).fetchone()[0]
            moment_count = conn.execute("SELECT COUNT(*) FROM moments WHERE user_id = ? AND status = 'normal'", (user.id,)).fetchone()[0]
        return {
            "user": dict(user_row),
            "product_count": product_count,
            "moment_count": moment_count,
            "bookings": self.list_my_bookings(),
            "tickets": self.list_my_tickets(),
        }

    def update_password(self, old_password: str, new_password: str) -> tuple[bool, str]:
        user = self.require_user()
        if len(new_password) < 8:
            return False, "新密码至少 8 位"
        with self.connect() as conn:
            row = conn.execute("SELECT password_hash FROM users WHERE id = ?", (user.id,)).fetchone()
            if row is None:
                return False, "原密码错误"
            stored = row["password_hash"]
            # 兼容旧格式
            if ":" not in stored:
                if stored != hashlib.sha256(old_password.encode("utf-8")).hexdigest():
                    return False, "原密码错误"
            else:
                if not verify_password(old_password, stored):
                    return False, "原密码错误"
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new_password), user.id))
        return True, "密码修改成功"

    def admin_summary(self) -> dict[str, Any]:
        self.require_admin()
        with self.connect() as conn:
            totals = {
                "users": conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
                "today_bookings": conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM bookings b JOIN venue_slots s ON s.id = b.slot_id
                    WHERE s.slot_date = ? AND b.status = 'active'
                    """,
                    (today_text(),),
                ).fetchone()[0],
                "products": conn.execute("SELECT COUNT(*) FROM products WHERE status = 'normal'").fetchone()[0],
                "moments": conn.execute("SELECT COUNT(*) FROM moments WHERE status = 'normal'").fetchone()[0],
                "activities": conn.execute("SELECT COUNT(*) FROM activities WHERE status = 'normal'").fetchone()[0],
                "total_bookings": conn.execute("SELECT COUNT(*) FROM bookings WHERE status = 'active'").fetchone()[0],
            }
            venue_hot = conn.execute(
                """
                SELECT v.name, COUNT(b.id) AS total
                FROM venues v
                JOIN venue_slots s ON s.venue_id = v.id
                LEFT JOIN bookings b ON b.slot_id = s.id AND b.status = 'active'
                GROUP BY v.id
                ORDER BY total DESC
                LIMIT 6
                """
            ).fetchall()
            recent_logs = conn.execute(
                """
                SELECT l.*, u.display_name AS admin_name
                FROM admin_logs l JOIN users u ON u.id = l.admin_id
                ORDER BY l.id DESC LIMIT 8
                """
            ).fetchall()
            # 近7天用户注册趋势
            reg_trend = []
            for i in range(6, -1, -1):
                day = (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
                count = conn.execute(
                    "SELECT COUNT(*) FROM users WHERE created_at LIKE ?",
                    (day + "%",),
                ).fetchone()[0]
                label = (date.today() - timedelta(days=i)).strftime("%m/%d")
                reg_trend.append((label, count))
        return {
            "totals": totals,
            "venue_hot": [dict(row) for row in venue_hot],
            "recent_logs": [dict(row) for row in recent_logs],
            "reg_trend": reg_trend,
        }

    def admin_users(self) -> list[dict[str, Any]]:
        self.require_admin()
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, username, display_name, role, status, college, created_at
                FROM users
                ORDER BY CASE role WHEN 'admin' THEN 0 WHEN 'teacher' THEN 1 ELSE 2 END, id ASC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def admin_set_user_status(self, user_id: int, status: str, reason: str = "") -> tuple[bool, str]:
        admin = self.require_admin()
        if user_id == admin.id:
            return False, "不能封禁当前管理员账号"
        if status not in {"active", "banned"}:
            return False, "状态不合法"
        with self.connect() as conn:
            row = conn.execute("SELECT display_name FROM users WHERE id = ?", (user_id,)).fetchone()
            if row is None:
                return False, "用户不存在"
            conn.execute("UPDATE users SET status = ? WHERE id = ?", (status, user_id))
        action = "解封用户" if status == "active" else "封禁用户"
        suffix = f"；原因：{reason}" if reason else ""
        self.log_admin(action, "user", user_id, f"{action}: {row['display_name']}{suffix}")
        logger.info("管理操作: %s user_id=%d by admin %d", action, user_id, admin.id)
        return True, f"{action}成功"

    def admin_products(self) -> list[dict[str, Any]]:
        self.require_admin()
        return self.list_products(include_removed=True)

    def admin_set_product_status(self, product_id: int, status: str, reason: str = "") -> tuple[bool, str]:
        self.require_admin()
        if status not in {"normal", "removed"}:
            return False, "状态不合法"
        with self.connect() as conn:
            row = conn.execute("SELECT title FROM products WHERE id = ?", (product_id,)).fetchone()
            if row is None:
                return False, "商品不存在"
            conn.execute("UPDATE products SET status = ? WHERE id = ?", (status, product_id))
        action = "恢复商品" if status == "normal" else "下架商品"
        suffix = f"；原因：{reason}" if reason else ""
        self.log_admin(action, "product", product_id, f"{action}: {row['title']}{suffix}")
        return True, f"{action}成功"

    def admin_bookings(self) -> list[dict[str, Any]]:
        self.require_admin()
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT b.id, b.status, b.created_at, b.updated_at,
                       u.display_name, u.username,
                       v.name, v.location, s.slot_date, s.slot_time
                FROM bookings b
                JOIN users u ON u.id = b.user_id
                JOIN venue_slots s ON s.id = b.slot_id
                JOIN venues v ON v.id = s.venue_id
                ORDER BY s.slot_date DESC, s.slot_time DESC, b.id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def admin_cancel_booking(self, booking_id: int, reason: str = "") -> tuple[bool, str]:
        self.require_admin()
        with self.connect() as conn:
            row = conn.execute("SELECT status FROM bookings WHERE id = ?", (booking_id,)).fetchone()
            if row is None:
                return False, "预约不存在"
            if row["status"] != "active":
                return False, "该预约已处理"
            conn.execute("UPDATE bookings SET status = 'admin_cancelled', updated_at = ? WHERE id = ?", (now_text(), booking_id))
        suffix = f"；原因：{reason}" if reason else ""
        self.log_admin("强制取消预约", "booking", booking_id, f"管理员取消预约 #{booking_id}{suffix}")
        return True, "预约已强制取消"

    def admin_activities(self) -> list[dict[str, Any]]:
        self.require_admin()
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT a.*, u.display_name AS organizer_name,
                       COUNT(ar.id) AS registered_count
                FROM activities a
                JOIN users u ON u.id = a.organizer_id
                LEFT JOIN activity_registrations ar ON ar.activity_id = a.id AND ar.status = 'active'
                GROUP BY a.id
                ORDER BY a.start_time DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def admin_cancel_activity(self, activity_id: int, reason: str = "") -> tuple[bool, str]:
        self.require_admin()
        with self.connect() as conn:
            row = conn.execute("SELECT title, status FROM activities WHERE id = ?", (activity_id,)).fetchone()
            if row is None:
                return False, "活动不存在"
            if row["status"] == "cancelled":
                return False, "活动已取消"
            conn.execute("UPDATE activities SET status = 'cancelled' WHERE id = ?", (activity_id,))
        suffix = f"；原因：{reason}" if reason else ""
        self.log_admin("取消活动", "activity", activity_id, f"取消活动: {row['title']}{suffix}")
        return True, "活动已取消"

    def admin_moments(self) -> list[dict[str, Any]]:
        self.require_admin()
        return self.list_moments(include_removed=True)

    def admin_set_moment_status(self, moment_id: int, status: str, reason: str = "") -> tuple[bool, str]:
        self.require_admin()
        if status not in {"normal", "removed"}:
            return False, "状态不合法"
        with self.connect() as conn:
            row = conn.execute("SELECT content FROM moments WHERE id = ?", (moment_id,)).fetchone()
            if row is None:
                return False, "动态不存在"
            conn.execute("UPDATE moments SET status = ? WHERE id = ?", (status, moment_id))
        action = "恢复动态" if status == "normal" else "删除动态"
        suffix = f"；原因：{reason}" if reason else ""
        self.log_admin(action, "moment", moment_id, f"{action}: {row['content'][:30]}{suffix}")
        return True, f"{action}成功"

    def admin_logs(self) -> list[dict[str, Any]]:
        self.require_admin()
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT l.*, u.display_name AS admin_name
                FROM admin_logs l JOIN users u ON u.id = l.admin_id
                ORDER BY l.id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]
