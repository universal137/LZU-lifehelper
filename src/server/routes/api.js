const {
  getDashboard,
  listMarketplaceItems,
  addMarketplaceItem,
  addMarketplaceMessage,
  listVenues,
  createBooking,
  listBookingsForCurrentUser,
  cancelBooking,
  listTransit,
  createTransitBooking,
  listActivities,
  addActivity,
  registerActivity,
  exportActivityRegistrations,
  listMoments,
  addMoment
} = require("../services/store");
const { getRequestParts, readJsonBody, sendJson, sendText } = require("../utils/http");

const validateRequired = (payload, fields) => {
  const missing = fields.filter((field) => !payload[field]);
  return missing.length === 0 ? null : `缺少字段: ${missing.join(", ")}`;
};

const handleApi = async (req, res) => {
  const { segments, query } = getRequestParts(req);

  try {
    if (req.method === "GET" && segments[1] === "dashboard") {
      sendJson(res, 200, getDashboard());
      return true;
    }

    if (req.method === "GET" && segments[1] === "marketplace") {
      sendJson(res, 200, listMarketplaceItems(query));
      return true;
    }

    if (req.method === "POST" && segments[1] === "marketplace" && segments.length === 2) {
      const payload = await readJsonBody(req);
      const error = validateRequired(payload, ["title", "category", "price", "description"]);
      if (error) {
        sendJson(res, 400, { message: error });
        return true;
      }
      sendJson(res, 201, addMarketplaceItem(payload));
      return true;
    }

    if (req.method === "POST" && segments[1] === "marketplace" && segments[3] === "messages") {
      const payload = await readJsonBody(req);
      const error = validateRequired(payload, ["content"]);
      if (error) {
        sendJson(res, 400, { message: error });
        return true;
      }
      const message = addMarketplaceMessage(segments[2], payload);
      if (!message) {
        sendJson(res, 404, { message: "商品不存在" });
        return true;
      }
      sendJson(res, 201, message);
      return true;
    }

    if (req.method === "GET" && segments[1] === "venues") {
      sendJson(res, 200, listVenues());
      return true;
    }

    if (req.method === "GET" && segments[1] === "bookings") {
      sendJson(res, 200, listBookingsForCurrentUser());
      return true;
    }

    if (req.method === "POST" && segments[1] === "bookings" && segments.length === 2) {
      const payload = await readJsonBody(req);
      const error = validateRequired(payload, ["venueId", "date", "time"]);
      if (error) {
        sendJson(res, 400, { message: error });
        return true;
      }
      const result = createBooking(payload);
      if (result.error) {
        sendJson(res, 409, { message: result.error });
        return true;
      }
      sendJson(res, 201, result.booking);
      return true;
    }

    if (req.method === "PATCH" && segments[1] === "bookings" && segments[3] === "cancel") {
      const booking = cancelBooking(segments[2]);
      if (!booking) {
        sendJson(res, 404, { message: "预约不存在" });
        return true;
      }
      sendJson(res, 200, booking);
      return true;
    }

    if (req.method === "GET" && segments[1] === "transit") {
      sendJson(res, 200, listTransit());
      return true;
    }

    if (req.method === "POST" && segments[1] === "transit" && segments[2] === "bookings") {
      const payload = await readJsonBody(req);
      const error = validateRequired(payload, ["scheduleId"]);
      if (error) {
        sendJson(res, 400, { message: error });
        return true;
      }
      const result = createTransitBooking(payload.scheduleId);
      if (result.error) {
        sendJson(res, 409, { message: result.error });
        return true;
      }
      sendJson(res, 201, result.booking);
      return true;
    }

    if (req.method === "GET" && segments[1] === "activities" && segments.length === 2) {
      sendJson(res, 200, listActivities());
      return true;
    }

    if (req.method === "POST" && segments[1] === "activities" && segments.length === 2) {
      const payload = await readJsonBody(req);
      const error = validateRequired(payload, ["title", "organizer", "location", "time", "capacity"]);
      if (error) {
        sendJson(res, 400, { message: error });
        return true;
      }
      sendJson(res, 201, addActivity(payload));
      return true;
    }

    if (req.method === "POST" && segments[1] === "activities" && segments[3] === "register") {
      const payload = await readJsonBody(req);
      const result = registerActivity(segments[2], payload.userName || "李同学");
      if (result.error) {
        sendJson(res, 409, { message: result.error });
        return true;
      }
      sendJson(res, 200, result.activity);
      return true;
    }

    if (req.method === "GET" && segments[1] === "activities" && segments[3] === "export") {
      const csv = exportActivityRegistrations(segments[2]);
      if (!csv) {
        sendJson(res, 404, { message: "活动不存在" });
        return true;
      }
      sendText(res, 200, csv, "text/csv; charset=utf-8");
      return true;
    }

    if (req.method === "GET" && segments[1] === "moments") {
      sendJson(res, 200, listMoments(query.tag));
      return true;
    }

    if (req.method === "POST" && segments[1] === "moments") {
      const payload = await readJsonBody(req);
      const error = validateRequired(payload, ["tag", "content"]);
      if (error) {
        sendJson(res, 400, { message: error });
        return true;
      }
      sendJson(res, 201, addMoment(payload));
      return true;
    }

    return false;
  } catch (error) {
    if (error.message === "INVALID_JSON") {
      sendJson(res, 400, { message: "JSON 格式错误" });
      return true;
    }
    sendJson(res, 500, { message: "服务器内部错误" });
    return true;
  }
};

module.exports = {
  handleApi
};
