const data = require("../data");

let sequence = 100;

const nextId = (prefix) => `${prefix}-${++sequence}`;

const normalizeKeyword = (value = "") => value.trim().toLowerCase();

const listMarketplaceItems = ({ keyword, category }) => {
  const normalizedKeyword = normalizeKeyword(keyword);
  return data.marketplaceItems
    .filter((item) => {
      const matchesKeyword = !normalizedKeyword
        || item.title.toLowerCase().includes(normalizedKeyword)
        || item.description.toLowerCase().includes(normalizedKeyword);
      const matchesCategory = !category || category === "全部" || item.category === category;
      return matchesKeyword && matchesCategory;
    })
    .sort((left, right) => new Date(right.createdAt) - new Date(left.createdAt));
};

const addMarketplaceItem = (payload) => {
  const item = {
    id: nextId("item"),
    title: payload.title,
    category: payload.category,
    price: Number(payload.price),
    sellerName: payload.sellerName || data.currentUser.name,
    description: payload.description,
    imageUrl: payload.imageUrl || "https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&w=600&q=80",
    createdAt: new Date().toISOString(),
    messages: []
  };
  data.marketplaceItems.unshift(item);
  return item;
};

const addMarketplaceMessage = (itemId, payload) => {
  const item = data.marketplaceItems.find((entry) => entry.id === itemId);
  if (!item) {
    return null;
  }
  const message = {
    id: nextId("msg"),
    userName: payload.userName || data.currentUser.name,
    content: payload.content,
    createdAt: new Date().toISOString()
  };
  item.messages.push(message);
  return message;
};

const listVenues = () => {
  return data.venues.map((venue) => ({
    ...venue,
    schedule: venue.schedule.map((day) => ({
      ...day,
      slots: day.slots.map((slot) => ({
        ...slot,
        available: slot.available && !data.bookings.some((booking) => (
          booking.venueId === venue.id
          && booking.date === day.date
          && booking.time === slot.time
          && booking.status === "confirmed"
        ))
      }))
    }))
  }));
};

const listBookingsForCurrentUser = () => {
  return data.bookings
    .filter((booking) => booking.userId === data.currentUser.id)
    .sort((left, right) => `${left.date}${left.time}`.localeCompare(`${right.date}${right.time}`));
};

const createBooking = (payload) => {
  const venue = data.venues.find((entry) => entry.id === payload.venueId);
  if (!venue) {
    return { error: "VENUE_NOT_FOUND" };
  }

  const day = venue.schedule.find((entry) => entry.date === payload.date);
  const slot = day?.slots.find((entry) => entry.time === payload.time);
  if (!slot || !slot.available) {
    return { error: "SLOT_NOT_AVAILABLE" };
  }

  const exists = data.bookings.some((booking) => (
    booking.venueId === payload.venueId
    && booking.date === payload.date
    && booking.time === payload.time
    && booking.status === "confirmed"
  ));
  if (exists) {
    return { error: "SLOT_ALREADY_BOOKED" };
  }

  const booking = {
    id: nextId("booking"),
    venueId: venue.id,
    venueName: venue.name,
    date: payload.date,
    time: payload.time,
    userId: data.currentUser.id,
    status: "confirmed"
  };
  data.bookings.push(booking);
  return { booking };
};

const cancelBooking = (bookingId) => {
  const booking = data.bookings.find((entry) => entry.id === bookingId && entry.userId === data.currentUser.id);
  if (!booking) {
    return null;
  }
  booking.status = "cancelled";
  return booking;
};

const listTransit = () => ({
  schedules: data.shuttleSchedules,
  bikeStations: data.bikeStations,
  bookings: data.transitBookings.filter((booking) => booking.userId === data.currentUser.id)
});

const createTransitBooking = (scheduleId) => {
  const schedule = data.shuttleSchedules.find((entry) => entry.id === scheduleId);
  if (!schedule) {
    return { error: "SCHEDULE_NOT_FOUND" };
  }
  if (schedule.seatsLeft <= 0) {
    return { error: "SEATS_EMPTY" };
  }
  schedule.seatsLeft -= 1;
  const booking = {
    id: nextId("busOrder"),
    scheduleId,
    route: schedule.route,
    departureTime: schedule.departureTime,
    userId: data.currentUser.id
  };
  data.transitBookings.push(booking);
  return { booking };
};

const listActivities = () => {
  return data.activities.map((activity) => ({
    ...activity,
    seatsLeft: activity.capacity - activity.registrations.length
  }));
};

const addActivity = (payload) => {
  const activity = {
    id: nextId("activity"),
    title: payload.title,
    organizer: payload.organizer,
    location: payload.location,
    time: payload.time,
    capacity: Number(payload.capacity),
    registrations: []
  };
  data.activities.unshift(activity);
  return activity;
};

const registerActivity = (activityId, userName) => {
  const activity = data.activities.find((entry) => entry.id === activityId);
  if (!activity) {
    return { error: "ACTIVITY_NOT_FOUND" };
  }
  if (activity.registrations.includes(userName)) {
    return { error: "ALREADY_REGISTERED" };
  }
  if (activity.registrations.length >= activity.capacity) {
    return { error: "ACTIVITY_FULL" };
  }
  activity.registrations.push(userName);
  return { activity };
};

const exportActivityRegistrations = (activityId) => {
  const activity = data.activities.find((entry) => entry.id === activityId);
  if (!activity) {
    return null;
  }
  return [
    "姓名,活动名称,时间,地点",
    ...activity.registrations.map((name) => `${name},${activity.title},${activity.time},${activity.location}`)
  ].join("\n");
};

const listMoments = (tag) => {
  return data.moments
    .filter((moment) => !tag || tag === "全部" || moment.tag === tag)
    .sort((left, right) => new Date(right.createdAt) - new Date(left.createdAt));
};

const addMoment = (payload) => {
  const moment = {
    id: nextId("moment"),
    author: payload.author || data.currentUser.name,
    tag: payload.tag,
    content: payload.content,
    createdAt: new Date().toISOString()
  };
  data.moments.unshift(moment);
  return moment;
};

const getDashboard = () => ({
  currentUser: data.currentUser,
  stats: {
    marketplaceCount: data.marketplaceItems.length,
    bookingCount: listBookingsForCurrentUser().filter((entry) => entry.status === "confirmed").length,
    upcomingActivities: listActivities().length,
    momentsCount: data.moments.length
  }
});

module.exports = {
  addActivity,
  addMarketplaceItem,
  addMarketplaceMessage,
  addMoment,
  cancelBooking,
  createBooking,
  createTransitBooking,
  exportActivityRegistrations,
  getDashboard,
  listActivities,
  listBookingsForCurrentUser,
  listMarketplaceItems,
  listMoments,
  listTransit,
  listVenues,
  registerActivity
};
