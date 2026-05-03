from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
import hashlib


def _today() -> str:
    return date.today().isoformat()


def _days_schedule(days: int) -> list[dict]:
    templates = ["08:00-09:00", "09:30-10:30", "14:00-15:00", "16:00-17:00", "19:00-20:00"]
    result: list[dict] = []
    for offset in range(days):
        current = date.today() + timedelta(days=offset)
        slots = []
        for index, time_range in enumerate(templates):
            slots.append({
                "time": time_range,
                "available": not (offset == 0 and index == 1),
            })
        result.append({"date": current.isoformat(), "slots": slots})
    return result


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@dataclass
class DesktopStore:
    current_user: dict | None = None
    users: list[dict] = field(default_factory=lambda: [
        {
            "id": "u1001",
            "username": "20230001",
            "name": "李同学",
            "role": "student",
            "role_label": "本科生",
            "college": "信息科学与工程学院",
            "password_hash": _hash_password("lzu123456"),
        },
        {
            "id": "u2001",
            "username": "club_admin",
            "name": "周同学",
            "role": "club_admin",
            "role_label": "社团管理员",
            "college": "学生社团联合会",
            "password_hash": _hash_password("club123456"),
        },
        {
            "id": "u9001",
            "username": "sys_admin",
            "name": "王老师",
            "role": "admin",
            "role_label": "系统管理员",
            "college": "网络与信息化办公室",
            "password_hash": _hash_password("admin123456"),
        },
    ])
    marketplace_items: list[dict] = field(default_factory=lambda: [
        {
            "id": "item-1",
            "title": "高等数学教材",
            "category": "书籍",
            "price": 25,
            "seller_name": "张同学",
            "seller_id": "u1002",
            "description": "八成新，榆中校区可面交，适合大一理工科同学。",
            "campus": "榆中校区",
            "status": "在售",
            "created_at": "2026-05-02 09:00",
            "messages": [
                {"user_name": "王同学", "content": "可以小刀吗？", "created_at": "2026-05-02 10:00"},
                {"user_name": "张同学", "content": "可以，校内面交 22 元。", "created_at": "2026-05-02 10:06"},
            ],
        },
        {
            "id": "item-2",
            "title": "九成新宿舍台灯",
            "category": "日用",
            "price": 38,
            "seller_name": "赵同学",
            "seller_id": "u1003",
            "description": "三档调光，带 USB 口，宿舍搬迁转让。",
            "campus": "城关校区",
            "status": "在售",
            "created_at": "2026-05-01 12:00",
            "messages": [],
        },
        {
            "id": "item-3",
            "title": "二手机械键盘",
            "category": "数码",
            "price": 129,
            "seller_name": "陈同学",
            "seller_id": "u1004",
            "description": "红轴，手感很好，带原装线，适合写代码。",
            "campus": "榆中校区",
            "status": "在售",
            "created_at": "2026-05-03 08:30",
            "messages": [{"user_name": "李同学", "content": "今晚图书馆门口能看货吗？", "created_at": "2026-05-03 09:10"}],
        },
    ])
    venues: list[dict] = field(default_factory=lambda: [
        {"id": "venue-1", "name": "羽毛球馆", "location": "榆中校区体育馆二层", "type": "体育场馆", "schedule": _days_schedule(3)},
        {"id": "venue-2", "name": "乒乓球馆", "location": "榆中校区体育馆一层", "type": "体育场馆", "schedule": _days_schedule(3)},
        {"id": "venue-3", "name": "教学楼 A201", "location": "天山堂 A 区", "type": "公共教室", "schedule": _days_schedule(3)},
    ])
    bookings: list[dict] = field(default_factory=lambda: [
        {
            "id": "booking-1",
            "venue_id": "venue-1",
            "venue_name": "羽毛球馆",
            "date": _today(),
            "time": "08:00-09:00",
            "user_id": "u1001",
            "status": "已预约",
        }
    ])
    shuttle_schedules: list[dict] = field(default_factory=lambda: [
        {"id": "bus-1", "route": "榆中校区 → 城关校区", "departure_time": "07:30", "seats_total": 40, "seats_left": 8, "station": "萃英大道东门"},
        {"id": "bus-2", "route": "城关校区 → 榆中校区", "departure_time": "12:30", "seats_total": 40, "seats_left": 15, "station": "医学部北门"},
        {"id": "bus-3", "route": "榆中校区 → 城关校区", "departure_time": "18:10", "seats_total": 40, "seats_left": 4, "station": "图书馆西侧"},
    ])
    bike_stations: list[dict] = field(default_factory=lambda: [
        {"name": "天山堂北门", "bikes_available": 12, "distance": "步行 2 分钟"},
        {"name": "图书馆东侧", "bikes_available": 6, "distance": "步行 5 分钟"},
        {"name": "体育馆南门", "bikes_available": 9, "distance": "步行 6 分钟"},
    ])
    transit_bookings: list[dict] = field(default_factory=list)
    activities: list[dict] = field(default_factory=lambda: [
        {
            "id": "activity-1",
            "title": "春季志愿服务宣讲",
            "organizer": "青年志愿者协会",
            "location": "大学生活动中心 201",
            "time": "2026-05-05 19:00",
            "capacity": 80,
            "registrations": ["李同学", "周同学"],
            "tag": "公益实践",
        },
        {
            "id": "activity-2",
            "title": "篮球社新生友谊赛",
            "organizer": "篮球社",
            "location": "西区篮球场",
            "time": "2026-05-07 16:00",
            "capacity": 30,
            "registrations": ["陈同学"],
            "tag": "体育竞技",
        },
    ])
    moments: list[dict] = field(default_factory=lambda: [
        {"author": "刘老师", "tag": "校园动态", "content": "图书馆自习区今天新增了插座位，晚间会比较紧张。", "created_at": "2026-05-03 08:30"},
        {"author": "马同学", "tag": "失物招领", "content": "在榆中校区食堂附近捡到校园卡一张，姓氏为王，请联系领取。", "created_at": "2026-05-03 09:15"},
        {"author": "周同学", "tag": "互助问答", "content": "请问城关校区自习室晚上几点关门？", "created_at": "2026-05-03 10:20"},
    ])

    def __post_init__(self) -> None:
        self._sequence = 100

    def _next_id(self, prefix: str) -> str:
        self._sequence += 1
        return f"{prefix}-{self._sequence}"

    def _require_user(self) -> dict:
        if self.current_user is None:
            raise RuntimeError("用户未登录")
        return self.current_user

    def list_demo_accounts(self) -> list[dict]:
        return [
            {"label": "学生账号 / 20230001 / lzu123456", "username": "20230001", "password": "lzu123456"},
            {"label": "社团管理员 / club_admin / club123456", "username": "club_admin", "password": "club123456"},
            {"label": "系统管理员 / sys_admin / admin123456", "username": "sys_admin", "password": "admin123456"},
        ]

    def login(self, username: str, password: str) -> tuple[bool, str]:
        account = next((user for user in self.users if user["username"] == username.strip()), None)
        if account is None:
            return False, "账号不存在"
        if account["password_hash"] != _hash_password(password):
            return False, "密码错误"
        self.current_user = {key: value for key, value in account.items() if key != "password_hash"}
        return True, "登录成功"

    def logout(self) -> None:
        self.current_user = None

    def change_password(self, old_password: str, new_password: str) -> tuple[bool, str]:
        user = self._require_user()
        for account in self.users:
            if account["id"] == user["id"]:
                if account["password_hash"] != _hash_password(old_password):
                    return False, "原密码错误"
                if len(new_password) < 8:
                    return False, "新密码至少 8 位"
                account["password_hash"] = _hash_password(new_password)
                return True, "密码修改成功"
        return False, "用户不存在"

    def dashboard(self) -> dict:
        user = self._require_user()
        return {
            "current_user": deepcopy(user),
            "stats": {
                "marketplace_count": len(self.marketplace_items),
                "booking_count": len([item for item in self.bookings if item["status"] == "已预约" and item["user_id"] == user["id"]]),
                "activity_count": len(self.activities),
                "moment_count": len(self.moments),
            },
            "notices": [
                "校车余票每天 07:00 更新。",
                "场馆预约支持未来 3 天时段。",
                "生活圈新增失物招领与互助问答标签。",
            ],
        }

    def service_shortcuts(self) -> list[dict]:
        return [
            {"title": "二手快转", "desc": "像闲鱼一样快速发布与沟通", "badge": "热门"},
            {"title": "校园服务", "desc": "参考今日校园的一站式办事入口", "badge": "推荐"},
            {"title": "生活圈", "desc": "借鉴社区产品的信息流展示", "badge": "社区"},
        ]

    def list_marketplace(self, keyword: str = "", category: str = "全部") -> list[dict]:
        keyword = keyword.strip().lower()
        result = []
        for item in self.marketplace_items:
            matches_keyword = not keyword or keyword in item["title"].lower() or keyword in item["description"].lower()
            matches_category = category in ("", "全部") or item["category"] == category
            if matches_keyword and matches_category:
                result.append(deepcopy(item))
        return result

    def add_marketplace_item(self, title: str, category: str, price: str, description: str, campus: str) -> None:
        user = self._require_user()
        self.marketplace_items.insert(0, {
            "id": self._next_id("item"),
            "title": title,
            "category": category,
            "price": float(price),
            "seller_name": user["name"],
            "seller_id": user["id"],
            "description": description,
            "campus": campus,
            "status": "在售",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "messages": [],
        })

    def add_message(self, item_id: str, content: str) -> bool:
        user = self._require_user()
        for item in self.marketplace_items:
            if item["id"] == item_id:
                item["messages"].append({
                    "user_name": user["name"],
                    "content": content,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                })
                return True
        return False

    def list_my_market_messages(self) -> list[dict]:
        user = self._require_user()
        rows: list[dict] = []
        for item in self.marketplace_items:
            for message in item["messages"]:
                if message["user_name"] == user["name"] or item["seller_id"] == user["id"]:
                    rows.append({
                        "item_title": item["title"],
                        "speaker": message["user_name"],
                        "content": message["content"],
                        "created_at": message["created_at"],
                    })
        return rows

    def list_venues(self) -> list[dict]:
        data = deepcopy(self.venues)
        for venue in data:
            for day in venue["schedule"]:
                for slot in day["slots"]:
                    occupied = any(
                        booking["venue_id"] == venue["id"]
                        and booking["date"] == day["date"]
                        and booking["time"] == slot["time"]
                        and booking["status"] == "已预约"
                        for booking in self.bookings
                    )
                    slot["available"] = slot["available"] and not occupied
        return data

    def list_bookings(self) -> list[dict]:
        user = self._require_user()
        return [deepcopy(item) for item in self.bookings if item["user_id"] == user["id"]]

    def create_booking(self, venue_id: str, booking_date: str, booking_time: str) -> tuple[bool, str]:
        user = self._require_user()
        venue = next((item for item in self.venues if item["id"] == venue_id), None)
        if venue is None:
            return False, "场馆不存在"
        for booking in self.bookings:
            if booking["venue_id"] == venue_id and booking["date"] == booking_date and booking["time"] == booking_time and booking["status"] == "已预约":
                return False, "该时段已被预约"
        self.bookings.append({
            "id": self._next_id("booking"),
            "venue_id": venue_id,
            "venue_name": venue["name"],
            "date": booking_date,
            "time": booking_time,
            "user_id": user["id"],
            "status": "已预约",
        })
        return True, "预约成功"

    def cancel_booking(self, booking_id: str) -> bool:
        user = self._require_user()
        for booking in self.bookings:
            if booking["id"] == booking_id and booking["user_id"] == user["id"] and booking["status"] == "已预约":
                booking["status"] = "已取消"
                return True
        return False

    def transit_snapshot(self) -> dict:
        user = self._require_user()
        return {
            "schedules": deepcopy(self.shuttle_schedules),
            "bike_stations": deepcopy(self.bike_stations),
            "bookings": [deepcopy(item) for item in self.transit_bookings if item["user_id"] == user["id"]],
        }

    def create_transit_booking(self, schedule_id: str) -> tuple[bool, str]:
        user = self._require_user()
        schedule = next((item for item in self.shuttle_schedules if item["id"] == schedule_id), None)
        if schedule is None:
            return False, "班次不存在"
        if schedule["seats_left"] <= 0:
            return False, "余票不足"
        schedule["seats_left"] -= 1
        self.transit_bookings.append({
            "id": self._next_id("bus"),
            "route": schedule["route"],
            "departure_time": schedule["departure_time"],
            "station": schedule["station"],
            "user_id": user["id"],
        })
        return True, "订票成功"

    def list_activities(self) -> list[dict]:
        result = deepcopy(self.activities)
        for item in result:
            item["seats_left"] = item["capacity"] - len(item["registrations"])
            item["registered"] = self.current_user is not None and self.current_user["name"] in item["registrations"]
        return result

    def add_activity(self, title: str, organizer: str, location: str, activity_time: str, capacity: str, tag: str) -> None:
        self._require_user()
        self.activities.insert(0, {
            "id": self._next_id("activity"),
            "title": title,
            "organizer": organizer,
            "location": location,
            "time": activity_time,
            "capacity": int(capacity),
            "registrations": [],
            "tag": tag,
        })

    def register_activity(self, activity_id: str) -> tuple[bool, str]:
        user = self._require_user()
        for activity in self.activities:
            if activity["id"] == activity_id:
                if user["name"] in activity["registrations"]:
                    return False, "你已经报名过了"
                if len(activity["registrations"]) >= activity["capacity"]:
                    return False, "活动人数已满"
                activity["registrations"].append(user["name"])
                return True, "报名成功"
        return False, "活动不存在"

    def export_activity(self, activity_id: str) -> str:
        activity = next((item for item in self.activities if item["id"] == activity_id), None)
        if activity is None:
            return ""
        rows = ["姓名,活动名称,时间,地点"]
        for name in activity["registrations"]:
            rows.append(f"{name},{activity['title']},{activity['time']},{activity['location']}")
        return "\n".join(rows)

    def list_moments(self, tag: str = "全部") -> list[dict]:
        if tag in ("", "全部"):
            return deepcopy(self.moments)
        return [deepcopy(item) for item in self.moments if item["tag"] == tag]

    def add_moment(self, author: str, tag: str, content: str) -> None:
        user = self._require_user()
        self.moments.insert(0, {
            "author": author or user["name"],
            "tag": tag,
            "content": content,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })

    def user_profile(self) -> dict:
        user = self._require_user()
        my_bookings = self.list_bookings()
        my_tickets = self.transit_snapshot()["bookings"]
        my_registered = [item for item in self.list_activities() if item["registered"]]
        return {
            "user": deepcopy(user),
            "bookings": my_bookings,
            "tickets": my_tickets,
            "activities": my_registered,
        }
