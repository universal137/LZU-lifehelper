const state = {
  marketFilter: { keyword: "", category: "全部" },
  momentFilter: { tag: "全部" }
};

const toast = document.getElementById("toast");

const showToast = (message) => {
  toast.textContent = message;
  toast.classList.add("is-visible");
  setTimeout(() => toast.classList.remove("is-visible"), 2200);
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

const setActivePanel = (target) => {
  document.querySelectorAll(".panel").forEach((panel) => {
    panel.classList.toggle("is-active", panel.dataset.panel === target);
  });
  document.querySelectorAll(".nav-item").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.target === target);
  });
};

const renderDashboard = async () => {
  const { currentUser, stats } = await api("/api/dashboard");
  document.getElementById("dashboardCards").innerHTML = `
    <div class="stat-card"><span>当前用户</span><strong>${currentUser.name}</strong></div>
    <div class="stat-card"><span>在售商品</span><strong>${stats.marketplaceCount}</strong></div>
    <div class="stat-card"><span>我的预约</span><strong>${stats.bookingCount}</strong></div>
    <div class="stat-card"><span>活动总数</span><strong>${stats.upcomingActivities}</strong></div>
  `;
  document.getElementById("profileView").innerHTML = `
    <h3>${currentUser.name}</h3>
    <p>角色：${currentUser.role}</p>
    <div class="summary-row">
      <div class="summary-card">商品数：${stats.marketplaceCount}</div>
      <div class="summary-card">预约数：${stats.bookingCount}</div>
      <div class="summary-card">活动数：${stats.upcomingActivities}</div>
      <div class="summary-card">动态数：${stats.momentsCount}</div>
    </div>
  `;
};

const renderMarketplace = async () => {
  const params = new URLSearchParams();
  if (state.marketFilter.keyword) {
    params.set("keyword", state.marketFilter.keyword);
  }
  if (state.marketFilter.category) {
    params.set("category", state.marketFilter.category);
  }
  const items = await api(`/api/marketplace?${params.toString()}`);
  document.getElementById("marketList").innerHTML = items.map((item) => `
    <article class="card">
      <img src="${item.imageUrl}" alt="${item.title}" />
      <div class="card-body">
        <div class="meta-row">
          <span class="meta-tag">${item.category}</span>
          <span class="meta-tag">${item.sellerName}</span>
        </div>
        <h3>${item.title}</h3>
        <p>${item.description}</p>
        <div class="price">¥${item.price}</div>
        <div class="sub-list">
          ${item.messages.map((message) => `<span class="slot">${message.userName}: ${message.content}</span>`).join("") || "<span class='slot is-disabled'>暂无留言</span>"}
        </div>
        <form class="action-row message-form" data-item-id="${item.id}">
          <input name="content" placeholder="留言咨询卖家" required />
          <button type="submit">留言</button>
        </form>
      </div>
    </article>
  `).join("");

  document.querySelectorAll(".message-form").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      try {
        await api(`/api/marketplace/${form.dataset.itemId}/messages`, {
          method: "POST",
          body: JSON.stringify({ content: formData.get("content") })
        });
        form.reset();
        showToast("留言已发送");
        renderMarketplace();
      } catch (error) {
        showToast(error.message);
      }
    });
  });
};

const renderBookings = async () => {
  const [venues, bookings] = await Promise.all([
    api("/api/venues"),
    api("/api/bookings")
  ]);

  document.getElementById("bookingSummary").innerHTML = bookings.map((booking) => `
    <div class="summary-card">
      ${booking.venueName} ${booking.date} ${booking.time} ${booking.status === "confirmed" ? "" : "(已取消)"}
      ${booking.status === "confirmed" ? `<button class="cancel-booking" data-booking-id="${booking.id}">取消</button>` : ""}
    </div>
  `).join("") || "<div class='summary-card'>当前没有预约记录</div>";

  document.getElementById("venueList").innerHTML = venues.map((venue) => `
    <article class="list-card">
      <h3>${venue.name}</h3>
      <p>${venue.location}</p>
      ${venue.schedule.map((day) => `
        <div>
          <strong>${day.date}</strong>
          <div class="sub-list">
            ${day.slots.map((slot) => slot.available
              ? `<button class="book-slot" data-venue-id="${venue.id}" data-date="${day.date}" data-time="${slot.time}">${slot.time}</button>`
              : `<span class="slot is-disabled">${slot.time} 已占用</span>`).join("")}
          </div>
        </div>
      `).join("")}
    </article>
  `).join("");

  document.querySelectorAll(".book-slot").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await api("/api/bookings", {
          method: "POST",
          body: JSON.stringify({
            venueId: button.dataset.venueId,
            date: button.dataset.date,
            time: button.dataset.time
          })
        });
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
        await api(`/api/bookings/${button.dataset.bookingId}/cancel`, {
          method: "PATCH"
        });
        showToast("预约已取消");
        renderBookings();
        renderDashboard();
      } catch (error) {
        showToast(error.message);
      }
    });
  });
};

const renderTransit = async () => {
  const data = await api("/api/transit");
  document.getElementById("transitList").innerHTML = `
    <div class="stack-list">
      ${data.schedules.map((item) => `
        <article class="list-card">
          <div class="meta-row">
            <span class="meta-tag">${item.route}</span>
            <span class="meta-tag">${item.departureTime}</span>
          </div>
          <p>余票：${item.seatsLeft}/${item.seatsTotal}</p>
          <button class="book-bus" data-schedule-id="${item.id}">预订座位</button>
        </article>
      `).join("")}
    </div>
    <div class="stack-list">
      <article class="list-card">
        <h3>共享单车站点</h3>
        ${data.bikeStations.map((station) => `<p>${station.name}：${station.bikesAvailable} 辆可用</p>`).join("")}
      </article>
      <article class="list-card">
        <h3>我的车票</h3>
        ${data.bookings.map((booking) => `<p>${booking.route} ${booking.departureTime}</p>`).join("") || "<p>暂无预订记录</p>"}
      </article>
    </div>
  `;

  document.querySelectorAll(".book-bus").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await api("/api/transit/bookings", {
          method: "POST",
          body: JSON.stringify({ scheduleId: button.dataset.scheduleId })
        });
        showToast("车票预订成功");
        renderTransit();
      } catch (error) {
        showToast(error.message);
      }
    });
  });
};

const renderActivities = async () => {
  const activities = await api("/api/activities");
  document.getElementById("activityList").innerHTML = activities.map((activity) => `
    <article class="list-card">
      <div class="meta-row">
        <span class="meta-tag">${activity.organizer}</span>
        <span class="meta-tag">剩余 ${activity.seatsLeft}</span>
      </div>
      <h3>${activity.title}</h3>
      <p>${activity.time} · ${activity.location}</p>
      <p>已报名：${activity.registrations.join("、") || "暂无"}</p>
      <div class="action-row">
        <button class="join-activity" data-activity-id="${activity.id}">报名参加</button>
        <button class="export-activity" data-activity-id="${activity.id}">导出名单</button>
      </div>
    </article>
  `).join("");

  document.querySelectorAll(".join-activity").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await api(`/api/activities/${button.dataset.activityId}/register`, {
          method: "POST",
          body: JSON.stringify({ userName: "李同学" })
        });
        showToast("报名成功");
        renderActivities();
      } catch (error) {
        showToast(error.message);
      }
    });
  });

  document.querySelectorAll(".export-activity").forEach((button) => {
    button.addEventListener("click", async () => {
      const response = await fetch(`/api/activities/${button.dataset.activityId}/export`);
      const text = await response.text();
      navigator.clipboard.writeText(text);
      showToast("名单 CSV 已复制");
    });
  });
};

const renderMoments = async () => {
  const params = new URLSearchParams();
  if (state.momentFilter.tag) {
    params.set("tag", state.momentFilter.tag);
  }
  const moments = await api(`/api/moments?${params.toString()}`);
  document.getElementById("momentList").innerHTML = moments.map((moment) => `
    <article class="list-card">
      <div class="meta-row">
        <span class="meta-tag">${moment.tag}</span>
        <span class="meta-tag">${moment.author}</span>
      </div>
      <p>${moment.content}</p>
      <small>${formatDateTime(moment.createdAt)}</small>
    </article>
  `).join("");
};

document.querySelectorAll(".nav-item").forEach((button) => {
  button.addEventListener("click", () => setActivePanel(button.dataset.target));
});

document.getElementById("marketSearchForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  state.marketFilter = {
    keyword: formData.get("keyword").trim(),
    category: formData.get("category")
  };
  renderMarketplace();
});

document.getElementById("marketCreateForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  try {
    await api("/api/marketplace", {
      method: "POST",
      body: JSON.stringify(Object.fromEntries(formData.entries()))
    });
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
  const formData = new FormData(event.currentTarget);
  try {
    await api("/api/activities", {
      method: "POST",
      body: JSON.stringify(Object.fromEntries(formData.entries()))
    });
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
  const formData = new FormData(event.currentTarget);
  try {
    await api("/api/moments", {
      method: "POST",
      body: JSON.stringify(Object.fromEntries(formData.entries()))
    });
    event.currentTarget.reset();
    showToast("动态已发布");
    renderMoments();
    renderDashboard();
  } catch (error) {
    showToast(error.message);
  }
});

const bootstrap = async () => {
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
