const STORAGE_KEYS = {
  favorites: "lzu-lifehelper:favorites",
  theme: "lzu-lifehelper:theme"
};

const state = {
  marketFilter: { keyword: "", category: "全部", sort: "latest" },
  momentFilter: { tag: "全部" },
  favorites: new Set(JSON.parse(localStorage.getItem(STORAGE_KEYS.favorites) || "[]")),
  dashboard: null
};

const toast = document.getElementById("toast");
const clockText = document.getElementById("clockText");
const themeToggle = document.getElementById("themeToggle");

const escapeHtml = (value = "") => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

const showToast = (message) => {
  toast.textContent = message;
  toast.classList.add("is-visible");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.remove("is-visible"), 2400);
};

const withBusy = async (element, task) => {
  const originalText = element?.textContent;
  if (element) {
    element.disabled = true;
    element.textContent = "处理中";
  }
  try {
    return await task();
  } finally {
    if (element) {
      element.disabled = false;
      element.textContent = originalText;
    }
  }
};

const api = async (path, options = {}) => {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json"
    },
    ...options
  });

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    throw new Error(data.message || "请求失败");
  }

  return data;
};

const formatDateTime = (value) => new Date(value).toLocaleString("zh-CN", {
  month: "numeric",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit"
});

const formatDateLabel = (value) => {
  const date = new Date(`${value}T00:00:00`);
  return date.toLocaleDateString("zh-CN", {
    month: "long",
    day: "numeric",
    weekday: "short"
  });
};

const saveFavorites = () => {
  localStorage.setItem(STORAGE_KEYS.favorites, JSON.stringify([...state.favorites]));
};

const emptyState = (title, body = "") => `
  <div class="empty-state">
    <div>
      <strong>${escapeHtml(title)}</strong>
      ${body ? `<p>${escapeHtml(body)}</p>` : ""}
    </div>
  </div>
`;

const errorState = (message) => `
  <div class="error-state">
    <div>
      <strong>加载失败</strong>
      <p>${escapeHtml(message)}</p>
    </div>
  </div>
`;

const setActivePanel = (target) => {
  document.querySelectorAll(".panel").forEach((panel) => {
    panel.classList.toggle("is-active", panel.dataset.panel === target);
  });
  document.querySelectorAll(".nav-item").forEach((button) => {
    const isActive = button.dataset.target === target;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
};

const updateClock = () => {
  clockText.textContent = new Date().toLocaleString("zh-CN", {
    month: "numeric",
    day: "numeric",
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit"
  });
};

const applyTheme = (theme) => {
  document.body.classList.toggle("theme-dark", theme === "dark");
  localStorage.setItem(STORAGE_KEYS.theme, theme);
};

const renderDashboard = async () => {
  const { currentUser, stats } = await api("/api/dashboard");
  state.dashboard = { currentUser, stats };

  document.getElementById("dashboardCards").innerHTML = [
    ["当前用户", currentUser.name],
    ["在售商品", stats.marketplaceCount],
    ["我的预约", stats.bookingCount],
    ["活动总数", stats.upcomingActivities]
  ].map(([label, value]) => `
    <div class="stat-card">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
    </div>
  `).join("");

  document.getElementById("insightStrip").innerHTML = `
    <span class="insight-pill">今日待办 ${stats.bookingCount} 项</span>
    <span class="insight-pill">收藏商品 ${state.favorites.size} 件</span>
    <span class="insight-pill">生活圈 ${stats.momentsCount} 条动态</span>
  `;

  document.getElementById("profileView").innerHTML = `
    <div class="profile-identity">
      <div class="avatar">${escapeHtml(currentUser.name.slice(0, 1))}</div>
      <h3>${escapeHtml(currentUser.name)}</h3>
      <p>角色：${escapeHtml(currentUser.role)}</p>
      <p>当前为演示账号，数据保存在服务端内存中。</p>
    </div>
    <div class="profile-metrics">
      <div class="metric-tile"><span>商品数</span><strong>${stats.marketplaceCount}</strong></div>
      <div class="metric-tile"><span>预约数</span><strong>${stats.bookingCount}</strong></div>
      <div class="metric-tile"><span>活动数</span><strong>${stats.upcomingActivities}</strong></div>
      <div class="metric-tile"><span>动态数</span><strong>${stats.momentsCount}</strong></div>
    </div>
  `;
};

const sortMarketplaceItems = (items) => {
  const sorted = [...items];
  if (state.marketFilter.sort === "priceAsc") {
    sorted.sort((left, right) => Number(left.price) - Number(right.price));
  } else if (state.marketFilter.sort === "priceDesc") {
    sorted.sort((left, right) => Number(right.price) - Number(left.price));
  }
  return sorted;
};

const renderMarketplace = async () => {
  const list = document.getElementById("marketList");
  list.innerHTML = emptyState("正在加载商品");
  const params = new URLSearchParams();
  if (state.marketFilter.keyword) {
    params.set("keyword", state.marketFilter.keyword);
  }
  if (state.marketFilter.category) {
    params.set("category", state.marketFilter.category);
  }

  try {
    const items = sortMarketplaceItems(await api(`/api/marketplace?${params.toString()}`));
    if (!items.length) {
      list.innerHTML = emptyState("没有找到匹配商品", "换个关键词或重置筛选后再试。");
      return;
    }

    list.innerHTML = items.map((item) => {
      const isFavorite = state.favorites.has(item.id);
      const messages = item.messages
        .slice(-2)
        .map((message) => `<span class="slot">${escapeHtml(message.userName)}：${escapeHtml(message.content)}</span>`)
        .join("");
      return `
        <article class="card">
          <div class="card-media">
            <div class="media-fallback">
              <span class="meta-tag">${escapeHtml(item.category)}</span>
              <strong>${escapeHtml(item.title)}</strong>
              <span>¥${escapeHtml(item.price)}</span>
            </div>
            <img src="${escapeHtml(item.imageUrl)}" alt="${escapeHtml(item.title)}" loading="eager" decoding="async" />
            <button class="favorite-button ${isFavorite ? "is-active" : ""}" type="button" data-item-id="${escapeHtml(item.id)}" aria-label="收藏商品">${isFavorite ? "♥" : "♡"}</button>
          </div>
          <div class="card-body">
            <div class="meta-row spread">
              <div class="meta-row">
                <span class="meta-tag">${escapeHtml(item.category)}</span>
                <span class="meta-tag">${escapeHtml(item.sellerName)}</span>
              </div>
              <span class="status-pill ${messages ? "is-ok" : ""}">${item.messages.length} 条留言</span>
            </div>
            <h3>${escapeHtml(item.title)}</h3>
            <p>${escapeHtml(item.description)}</p>
            <div class="price">¥${escapeHtml(item.price)}</div>
            <div class="sub-list">
              ${messages || "<span class='slot is-disabled'>暂无留言</span>"}
            </div>
            <form class="action-row message-form" data-item-id="${escapeHtml(item.id)}">
              <input name="content" placeholder="留言咨询卖家" required />
              <button type="submit">留言</button>
            </form>
          </div>
        </article>
      `;
    }).join("");

    document.querySelectorAll(".favorite-button").forEach((button) => {
      button.addEventListener("click", () => {
        const id = button.dataset.itemId;
        if (state.favorites.has(id)) {
          state.favorites.delete(id);
          showToast("已取消收藏");
        } else {
          state.favorites.add(id);
          showToast("已加入收藏");
        }
        saveFavorites();
        renderMarketplace();
        if (state.dashboard) {
          renderDashboardFromCache();
        }
      });
    });

    document.querySelectorAll(".message-form").forEach((form) => {
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const button = form.querySelector("button");
        const formData = new FormData(form);
        try {
          await withBusy(button, () => api(`/api/marketplace/${form.dataset.itemId}/messages`, {
            method: "POST",
            body: JSON.stringify({ content: formData.get("content") })
          }));
          form.reset();
          showToast("留言已发送");
          renderMarketplace();
        } catch (error) {
          showToast(error.message);
        }
      });
    });
  } catch (error) {
    list.innerHTML = errorState(error.message);
  }
};

const renderDashboardFromCache = () => {
  if (!state.dashboard) {
    return;
  }
  const { currentUser, stats } = state.dashboard;
  document.getElementById("insightStrip").innerHTML = `
    <span class="insight-pill">今日待办 ${stats.bookingCount} 项</span>
    <span class="insight-pill">收藏商品 ${state.favorites.size} 件</span>
    <span class="insight-pill">生活圈 ${stats.momentsCount} 条动态</span>
  `;
};

const renderBookings = async () => {
  const summary = document.getElementById("bookingSummary");
  const venueList = document.getElementById("venueList");
  summary.innerHTML = emptyState("正在加载预约");
  venueList.innerHTML = "";

  try {
    const [venues, bookings] = await Promise.all([
      api("/api/venues"),
      api("/api/bookings")
    ]);

    summary.innerHTML = bookings.map((booking) => `
      <div class="summary-card">
        <div>
          <strong>${escapeHtml(booking.venueName)}</strong>
          <p>${escapeHtml(formatDateLabel(booking.date))} ${escapeHtml(booking.time)}</p>
        </div>
        ${booking.status === "confirmed"
          ? `<button class="cancel-booking secondary-button" type="button" data-booking-id="${escapeHtml(booking.id)}">取消</button>`
          : "<span class='status-pill'>已取消</span>"}
      </div>
    `).join("") || emptyState("当前没有预约记录", "可从下方场馆时段中选择一个预约。");

    venueList.innerHTML = venues.map((venue) => `
      <article class="list-card">
        <div class="list-card-header">
          <div>
            <h3>${escapeHtml(venue.name)}</h3>
            <p>${escapeHtml(venue.location)}</p>
          </div>
          <span class="status-pill is-ok">未来 3 天</span>
        </div>
        ${venue.schedule.map((day) => {
          const availableCount = day.slots.filter((slot) => slot.available).length;
          return `
            <div>
              <div class="meta-row spread">
                <strong>${escapeHtml(formatDateLabel(day.date))}</strong>
                <span class="status-pill ${availableCount ? "is-ok" : "is-danger"}">可约 ${availableCount}</span>
              </div>
              <div class="sub-list">
                ${day.slots.map((slot) => slot.available
                  ? `<button class="book-slot" type="button" data-venue-id="${escapeHtml(venue.id)}" data-date="${escapeHtml(day.date)}" data-time="${escapeHtml(slot.time)}">${escapeHtml(slot.time)}</button>`
                  : `<span class="slot is-disabled">${escapeHtml(slot.time)} 已占用</span>`).join("")}
              </div>
            </div>
          `;
        }).join("")}
      </article>
    `).join("");

    document.querySelectorAll(".book-slot").forEach((button) => {
      button.addEventListener("click", async () => {
        try {
          await withBusy(button, () => api("/api/bookings", {
            method: "POST",
            body: JSON.stringify({
              venueId: button.dataset.venueId,
              date: button.dataset.date,
              time: button.dataset.time
            })
          }));
          showToast("预约成功");
          renderBookings();
          renderDashboard();
        } catch (error) {
          showToast(error.message);
        }
      });
    });

    document.querySelectorAll(".cancel-booking").forEach((button) => {
      button.addEventListener("click", async () => {
        try {
          await withBusy(button, () => api(`/api/bookings/${button.dataset.bookingId}/cancel`, {
            method: "PATCH"
          }));
          showToast("预约已取消");
          renderBookings();
          renderDashboard();
        } catch (error) {
          showToast(error.message);
        }
      });
    });
  } catch (error) {
    summary.innerHTML = errorState(error.message);
  }
};

const renderTransit = async () => {
  const list = document.getElementById("transitList");
  list.innerHTML = emptyState("正在加载出行信息");

  try {
    const data = await api("/api/transit");
    list.innerHTML = `
      <div class="stack-list">
        ${data.schedules.map((item) => {
          const ratio = Math.max(0, Math.min(1, item.seatsLeft / item.seatsTotal));
          const fillClass = item.seatsLeft === 0 ? "is-empty" : item.seatsLeft <= 5 ? "is-low" : "";
          return `
            <article class="list-card">
              <div class="meta-row spread">
                <div>
                  <h3>${escapeHtml(item.route)}</h3>
                  <p>${escapeHtml(item.departureTime)} 发车</p>
                </div>
                <span class="status-pill ${item.seatsLeft > 5 ? "is-ok" : item.seatsLeft ? "is-warn" : "is-danger"}">余票 ${item.seatsLeft}</span>
              </div>
              <div class="availability-bar"><span class="availability-fill ${fillClass}" style="width: ${ratio * 100}%"></span></div>
              <p>${escapeHtml(item.seatsLeft)}/${escapeHtml(item.seatsTotal)} 个座位可用</p>
              <div class="action-row">
                <button class="book-bus" type="button" data-schedule-id="${escapeHtml(item.id)}" ${item.seatsLeft <= 0 ? "disabled" : ""}>预订座位</button>
              </div>
            </article>
          `;
        }).join("")}
      </div>
      <div class="stack-list">
        <article class="list-card">
          <h3>共享单车站点</h3>
          ${data.bikeStations.map((station) => `
            <div class="summary-card">
              <strong>${escapeHtml(station.name)}</strong>
              <span class="status-pill ${station.bikesAvailable > 8 ? "is-ok" : "is-warn"}">${escapeHtml(station.bikesAvailable)} 辆可用</span>
            </div>
          `).join("")}
        </article>
        <article class="list-card">
          <h3>我的车票</h3>
          ${data.bookings.map((booking) => `<p>${escapeHtml(booking.route)} ${escapeHtml(booking.departureTime)}</p>`).join("") || "<p>暂无预订记录</p>"}
        </article>
      </div>
    `;

    document.querySelectorAll(".book-bus").forEach((button) => {
      button.addEventListener("click", async () => {
        try {
          await withBusy(button, () => api("/api/transit/bookings", {
            method: "POST",
            body: JSON.stringify({ scheduleId: button.dataset.scheduleId })
          }));
          showToast("车票预订成功");
          renderTransit();
        } catch (error) {
          showToast(error.message);
        }
      });
    });
  } catch (error) {
    list.innerHTML = errorState(error.message);
  }
};

const renderActivities = async () => {
  const list = document.getElementById("activityList");
  list.innerHTML = emptyState("正在加载活动");

  try {
    const activities = await api("/api/activities");
    list.innerHTML = activities.map((activity) => {
      const capacity = Number(activity.capacity) || activity.registrations.length + activity.seatsLeft;
      const registered = capacity - activity.seatsLeft;
      const ratio = capacity > 0 ? registered / capacity : 0;
      return `
        <article class="list-card">
          <div class="list-card-header">
            <div>
              <div class="meta-row">
                <span class="meta-tag">${escapeHtml(activity.organizer)}</span>
                <span class="meta-tag">${escapeHtml(activity.time)}</span>
              </div>
              <h3>${escapeHtml(activity.title)}</h3>
              <p>${escapeHtml(activity.location)}</p>
            </div>
            <span class="status-pill ${activity.seatsLeft ? "is-ok" : "is-danger"}">剩余 ${escapeHtml(activity.seatsLeft)}</span>
          </div>
          <div class="availability-bar"><span class="availability-fill ${activity.seatsLeft ? "" : "is-empty"}" style="width: ${ratio * 100}%"></span></div>
          <p>已报名：${activity.registrations.map(escapeHtml).join("、") || "暂无"}</p>
          <div class="action-row">
            <button class="join-activity" type="button" data-activity-id="${escapeHtml(activity.id)}" ${activity.seatsLeft <= 0 ? "disabled" : ""}>报名参加</button>
            <button class="export-activity secondary-button" type="button" data-activity-id="${escapeHtml(activity.id)}">导出名单</button>
          </div>
        </article>
      `;
    }).join("") || emptyState("暂无活动", "可发布新的社团活动。");

    document.querySelectorAll(".join-activity").forEach((button) => {
      button.addEventListener("click", async () => {
        try {
          await withBusy(button, () => api(`/api/activities/${button.dataset.activityId}/register`, {
            method: "POST",
            body: JSON.stringify({ userName: "李同学" })
          }));
          showToast("报名成功");
          renderActivities();
          renderDashboard();
        } catch (error) {
          showToast(error.message);
        }
      });
    });

    document.querySelectorAll(".export-activity").forEach((button) => {
      button.addEventListener("click", async () => {
        const response = await fetch(`/api/activities/${button.dataset.activityId}/export`);
        const text = await response.text();
        await navigator.clipboard.writeText(text);
        showToast("名单 CSV 已复制");
      });
    });
  } catch (error) {
    list.innerHTML = errorState(error.message);
  }
};

const renderMoments = async () => {
  const list = document.getElementById("momentList");
  list.innerHTML = emptyState("正在加载动态");
  const params = new URLSearchParams();
  if (state.momentFilter.tag) {
    params.set("tag", state.momentFilter.tag);
  }

  try {
    const moments = await api(`/api/moments?${params.toString()}`);
    list.innerHTML = moments.map((moment) => `
      <article class="list-card">
        <div class="meta-row spread">
          <div class="meta-row">
            <span class="meta-tag">${escapeHtml(moment.tag)}</span>
            <span class="meta-tag">${escapeHtml(moment.author)}</span>
          </div>
          <span class="status-pill">${escapeHtml(formatDateTime(moment.createdAt))}</span>
        </div>
        <p>${escapeHtml(moment.content)}</p>
      </article>
    `).join("") || emptyState("暂无动态", "发布第一条校园动态。");
  } catch (error) {
    list.innerHTML = errorState(error.message);
  }
};

document.querySelectorAll(".nav-item").forEach((button) => {
  button.addEventListener("click", () => setActivePanel(button.dataset.target));
});

document.getElementById("marketSearchForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  state.marketFilter = {
    keyword: formData.get("keyword").trim(),
    category: formData.get("category"),
    sort: formData.get("sort")
  };
  renderMarketplace();
});

document.getElementById("marketClearButton").addEventListener("click", () => {
  const form = document.getElementById("marketSearchForm");
  form.reset();
  state.marketFilter = { keyword: "", category: "全部", sort: "latest" };
  renderMarketplace();
});

document.getElementById("marketCreateForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.currentTarget.querySelector("button");
  const formData = new FormData(event.currentTarget);
  try {
    await withBusy(button, () => api("/api/marketplace", {
      method: "POST",
      body: JSON.stringify(Object.fromEntries(formData.entries()))
    }));
    event.currentTarget.reset();
    showToast("商品已发布");
    renderMarketplace();
    renderDashboard();
  } catch (error) {
    showToast(error.message);
  }
});

document.getElementById("activityForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.currentTarget.querySelector("button");
  const formData = new FormData(event.currentTarget);
  try {
    await withBusy(button, () => api("/api/activities", {
      method: "POST",
      body: JSON.stringify(Object.fromEntries(formData.entries()))
    }));
    event.currentTarget.reset();
    showToast("活动已发布");
    renderActivities();
    renderDashboard();
  } catch (error) {
    showToast(error.message);
  }
});

document.getElementById("momentFilterForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  state.momentFilter = { tag: formData.get("tag") };
  renderMoments();
});

document.getElementById("momentForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.currentTarget.querySelector("button");
  const formData = new FormData(event.currentTarget);
  try {
    await withBusy(button, () => api("/api/moments", {
      method: "POST",
      body: JSON.stringify(Object.fromEntries(formData.entries()))
    }));
    event.currentTarget.reset();
    showToast("动态已发布");
    renderMoments();
    renderDashboard();
  } catch (error) {
    showToast(error.message);
  }
});

themeToggle.addEventListener("click", () => {
  const nextTheme = document.body.classList.contains("theme-dark") ? "light" : "dark";
  applyTheme(nextTheme);
});

const bootstrap = async () => {
  applyTheme(localStorage.getItem(STORAGE_KEYS.theme) || "light");
  updateClock();
  setInterval(updateClock, 1000 * 30);
  await Promise.all([
    renderDashboard(),
    renderMarketplace(),
    renderBookings(),
    renderTransit(),
    renderActivities(),
    renderMoments()
  ]);
};

bootstrap().catch((error) => {
  showToast(error.message);
});
