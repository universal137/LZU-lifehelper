const now = new Date();

const addDays = (date, days) => {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
};

const formatDate = (date) => date.toISOString().slice(0, 10);

const buildSlots = () => {
  const templates = ["08:00-09:00", "09:00-10:00", "14:00-15:00", "15:00-16:00", "19:00-20:00"];
  return Array.from({ length: 3 }, (_, index) => {
    const day = addDays(now, index);
    return {
      date: formatDate(day),
      slots: templates.map((time, slotIndex) => ({
        time,
        available: !(index === 0 && slotIndex === 1)
      }))
    };
  });
};

module.exports = {
  currentUser: {
    id: "u1001",
    name: "李同学",
    role: "student"
  },
  marketplaceItems: [
    {
      id: "item-1",
      title: "高等数学教材",
      category: "书籍",
      price: 25,
      sellerName: "张同学",
      description: "八成新，榆中校区可面交。",
      imageUrl: "https://images.unsplash.com/photo-1521587760476-6c12a4b040da?auto=format&fit=crop&w=600&q=80",
      createdAt: "2026-05-02T09:00:00.000Z",
      messages: [
        {
          id: "msg-1",
          userName: "王同学",
          content: "可以小刀吗？",
          createdAt: "2026-05-02T10:00:00.000Z"
        }
      ]
    },
    {
      id: "item-2",
      title: "九成新台灯",
      category: "日用",
      price: 38,
      sellerName: "赵同学",
      description: "宿舍搬迁转让，光线稳定。",
      imageUrl: "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=600&q=80",
      createdAt: "2026-05-01T12:00:00.000Z",
      messages: []
    }
  ],
  venues: [
    {
      id: "venue-1",
      name: "羽毛球馆",
      location: "榆中校区体育馆二层",
      schedule: buildSlots()
    },
    {
      id: "venue-2",
      name: "乒乓球馆",
      location: "榆中校区体育馆一层",
      schedule: buildSlots()
    },
    {
      id: "venue-3",
      name: "教学楼 A201",
      location: "天山堂 A 区",
      schedule: buildSlots()
    }
  ],
  bookings: [
    {
      id: "booking-1",
      venueId: "venue-1",
      venueName: "羽毛球馆",
      date: formatDate(now),
      time: "08:00-09:00",
      userId: "u1001",
      status: "confirmed"
    }
  ],
  shuttleSchedules: [
    {
      id: "bus-1",
      route: "榆中校区 → 城关校区",
      departureTime: "07:30",
      seatsTotal: 40,
      seatsLeft: 8
    },
    {
      id: "bus-2",
      route: "城关校区 → 榆中校区",
      departureTime: "12:30",
      seatsTotal: 40,
      seatsLeft: 15
    },
    {
      id: "bus-3",
      route: "榆中校区 → 城关校区",
      departureTime: "18:10",
      seatsTotal: 40,
      seatsLeft: 4
    }
  ],
  bikeStations: [
    {
      id: "bike-1",
      name: "天山堂北门",
      bikesAvailable: 12
    },
    {
      id: "bike-2",
      name: "图书馆东侧",
      bikesAvailable: 6
    }
  ],
  transitBookings: [],
  activities: [
    {
      id: "activity-1",
      title: "春季志愿服务宣讲",
      organizer: "青年志愿者协会",
      location: "大学生活动中心 201",
      time: "2026-05-05 19:00",
      capacity: 80,
      registrations: ["李同学", "周同学"]
    },
    {
      id: "activity-2",
      title: "篮球社新生友谊赛",
      organizer: "篮球社",
      location: "西区篮球场",
      time: "2026-05-07 16:00",
      capacity: 30,
      registrations: ["陈同学"]
    }
  ],
  moments: [
    {
      id: "moment-1",
      author: "刘老师",
      tag: "校园动态",
      content: "图书馆自习区今天新增了插座位，晚间会比较紧张。",
      createdAt: "2026-05-03T08:30:00.000Z"
    },
    {
      id: "moment-2",
      author: "马同学",
      tag: "失物招领",
      content: "在榆中校区食堂附近捡到校园卡一张，姓氏为王，请联系领取。",
      createdAt: "2026-05-03T09:15:00.000Z"
    }
  ]
};
