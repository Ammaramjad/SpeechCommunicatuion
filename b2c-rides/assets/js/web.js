const TYPE_BY_NAV = {
  home: "airport_pickup",
  pickup: "airport_pickup",
  drop: "airport_drop",
  p2p: "p2p",
  hourly: "hourly",
  rental: "rental",
  taxi: "instant",
};

const state = {
  catalog: null,
  live: null,
  type: "airport_pickup",
  quote: null,
  vehicle: null,
  booking: null,
  tripFilter: "all",
  form: {
    from_id: "tpe",
    to_id: "taipei-main",
    when: "",
    pax: 2,
    bags: 2,
    hours: 8,
    days: 2,
    meet: true,
    child_seat: false,
    english: false,
    pet: false,
    insurance: false,
    one_way_rental: false,
    roundtrip: false,
    promo: "",
    name: "林小華",
    phone: "0912-000-888",
    flight: "CI 011",
    pay: "card",
    channel: "web",
  },
};

function tomorrow10() {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  d.setHours(10, 0, 0, 0);
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}

function place(id) {
  return state.catalog.places.find((p) => p.id === id);
}

function opts(places, selected) {
  return places.map((p) => `<option value="${p.id}" ${p.id === selected ? "selected" : ""}>${RL.loc(p)}</option>`).join("");
}

function setActiveNav(view) {
  document.querySelectorAll("[data-nav]").forEach((a) => {
    a.classList.toggle("active", a.dataset.go === view || (view === "home" && a.dataset.go === "pickup" && state.type === "airport_pickup"));
  });
}

function applyTypeDefaults() {
  if (state.type === "airport_drop") {
    state.form.from_id = "xinyi";
    state.form.to_id = "tpe";
  } else if (state.type === "airport_pickup") {
    state.form.from_id = "tpe";
    state.form.to_id = "taipei-main";
  } else if (state.type === "hourly") {
    state.form.from_id = "xinyi";
    state.form.to_id = "jiufen";
  } else if (state.type === "rental") {
    state.form.from_id = "tpe";
    state.form.to_id = "tpe";
  } else if (state.type === "instant") {
    state.form.from_id = "taipei-main";
    state.form.to_id = "xinyi";
  }
}

function extras() {
  const f = state.form;
  const rentalBits = state.type === "rental"
    ? `<label><input type="checkbox" data-k="insurance" ${f.insurance ? "checked" : ""}/> ${RL.t("insurance")}</label>
       <label><input type="checkbox" data-k="one_way_rental" ${f.one_way_rental ? "checked" : ""}/> ${RL.t("oneway")}</label>`
    : "";
  return `
    <div class="checks">
      <label><input type="checkbox" data-k="meet" ${f.meet ? "checked" : ""}/> ${RL.t("meet")}</label>
      <label><input type="checkbox" data-k="child_seat" ${f.child_seat ? "checked" : ""}/> ${RL.t("child")}</label>
      <label><input type="checkbox" data-k="english" ${f.english ? "checked" : ""}/> ${RL.t("english")}</label>
      <label><input type="checkbox" data-k="pet" ${f.pet ? "checked" : ""}/> ${RL.t("pet")}</label>
      <label><input type="checkbox" data-k="roundtrip" ${f.roundtrip ? "checked" : ""}/> ${RL.t("roundtrip")}</label>
      ${rentalBits}
    </div>`;
}

function searchForm() {
  const f = state.form;
  const extraHour = state.type === "hourly" ? `<div class="field">${RL.t("hours")}<input type="number" min="4" max="12" value="${f.hours}" data-k="hours"/></div>` : "";
  const extraDay = state.type === "rental" ? `<div class="field">${RL.t("days")}<input type="number" min="1" max="14" value="${f.days}" data-k="days"/></div>` : "";
  const titles = {
    airport_pickup: RL.t("pickup"),
    airport_drop: RL.t("drop"),
    p2p: RL.t("p2p"),
    hourly: RL.t("hourly"),
    rental: RL.t("rental"),
    instant: RL.t("taxi"),
  };
  return `
    <div class="tabs">
      ${[["airport_pickup","pickup"],["airport_drop","drop"],["p2p","p2p"],["hourly","hourly"],["rental","rental"],["instant","taxi"]].map(([id,k]) =>
        `<button class="tab ${state.type===id?"on":""}" data-type="${id}" type="button">${RL.t(k)}</button>`).join("")}
    </div>
    <p class="kicker">${titles[state.type] || ""}</p>
    <div class="g5">
      <div class="field">${RL.t("from")}<select data-k="from_id">${opts(state.catalog.places, f.from_id)}</select></div>
      <div class="field">${RL.t("to")}<select data-k="to_id">${opts(state.catalog.places, f.to_id)}</select></div>
      <div class="field">${RL.t("when")}<input type="datetime-local" data-k="when" value="${f.when}"/></div>
      <div class="field">${RL.t("pax")}<input type="number" min="1" max="50" value="${f.pax}" data-k="pax"/></div>
      ${extraHour}${extraDay}
      <button class="btn btn-k" id="goSearch" type="button">${RL.t("search")}</button>
    </div>
    ${extras()}
    <div class="checks"><label>${RL.t("promo")} <input data-k="promo" value="${f.promo}" placeholder="WELCOME / TPE200 / FAMILY" style="min-width:180px"/></label></div>
  `;
}

function bindForm(root) {
  root.querySelectorAll("[data-k]").forEach((el) => {
    const apply = () => {
      const k = el.dataset.k;
      state.form[k] = el.type === "checkbox" ? el.checked : (el.type === "number" ? Number(el.value) : el.value);
    };
    el.addEventListener("change", apply);
    el.addEventListener("input", apply);
  });
}

function liveCard(c) {
  return `<article class="card live-card" data-route="${c.id}">
    <img src="${c.img}" alt=""/>
    <div class="pad">
      <div class="live-row">
        <span class="badge">${c.mins} min</span>
        ${c.surge ? `<span class="badge surge">surge</span>` : ""}
        <span class="meta">★ ${c.rating}</span>
      </div>
      <h3>${RL.loc(c.from_place)} → ${RL.loc(c.to_place)}</h3>
      <div class="occ"><i style="width:${Math.min(100, 20 + c.booked_today * 18)}%"></i></div>
      <p class="meta">${c.available} ${RL.t("carsLeft")} · ${c.booked_today} ${RL.t("bookedToday")}</p>
      <div class="price">${RL.nt(c.live_price)} 起</div>
      <button class="pill wish" data-wish="${c.id}" type="button">${c.saved ? "♥" : "♡"} ${RL.t("wish")}</button>
    </div></article>`;
}

async function refreshLive() {
  state.live = await API.get("/api/live/marketplace");
}

async function show(view) {
  const root = document.getElementById("view");
  setActiveNav(view);
  location.hash = view;

  if (view === "home" || view === "pickup" || view === "drop" || view === "p2p" || view === "hourly" || view === "rental") {
    if (TYPE_BY_NAV[view]) state.type = TYPE_BY_NAV[view];
    if (view !== "home") applyTypeDefaults();
    await refreshLive();
    const cards = state.live.cards.filter((c) => {
      if (state.type === "airport_drop") return c.to === "tpe" || c.to === "tsa" || c.to === "khh" || c.to === "rmq";
      if (state.type === "rental") return true;
      return true;
    });
    root.innerHTML = `
      <section class="hero"><div class="wrap">
        <h1>${RL.t("hero")}</h1><p>${RL.t("heroSub")}</p>
        <div class="search">${searchForm()}</div>
      </div></section>
      <section class="sec wrap">
        <h2>${RL.t("liveBoard")}</h2>
        <p class="sub">${RL.t("liveHint")} · ${new Date(state.live.updated_at).toLocaleTimeString()}</p>
        <div class="grid4" id="routes">${cards.map(liveCard).join("")}</div>
      </section>
      <section class="sec wrap" style="padding-top:0">
        <h2>${RL.t("reviews")}</h2>
        <div class="grid4" style="grid-template-columns:repeat(3,1fr)">
          ${state.live.reviews.map((r) => `<div class="panel"><b>★ ${r.stars} ${r.name}</b><p class="sub">${r.route}<br/>${RL.lang==="en"?r.text_en:r.text_zh}</p></div>`).join("")}
        </div>
      </section>`;
    bindForm(root);
    root.querySelectorAll("[data-type]").forEach((t) => t.onclick = () => {
      state.type = t.dataset.type;
      applyTypeDefaults();
      show(state.type === "instant" ? "taxi" : "home");
    });
    root.querySelectorAll("[data-route]").forEach((el) => el.onclick = (ev) => {
      if (ev.target.closest("[data-wish]")) return;
      const r = state.live.cards.find((x) => x.id === el.dataset.route);
      state.form.from_id = r.from; state.form.to_id = r.to;
      show("results");
    });
    root.querySelectorAll("[data-wish]").forEach((btn) => btn.onclick = async (e) => {
      e.stopPropagation();
      await API.post("/api/wishlist", { route_id: btn.dataset.wish });
      show(view);
    });
    document.getElementById("goSearch").onclick = () => show(state.type === "instant" ? "taxi" : "results");
    return;
  }

  if (view === "results") {
    const list = state.type === "rental" ? state.catalog.rentals : state.catalog.vehicles;
    root.innerHTML = `<div class="wrap split">
      <aside class="filters">
        <button class="pill" id="back">${RL.t("home")}</button>
        <h3>${RL.t("results")}</h3>
        <p class="sub">${RL.loc(place(state.form.from_id))} → ${RL.loc(place(state.form.to_id))}</p>
        <label class="meta">${RL.t("sort")}
          <select id="sort"><option value="price">NT$</option><option value="seats">${RL.t("pax")}</option></select>
        </label>
      </aside>
      <div id="list"></div>
    </div>`;
    const box = document.getElementById("list");
    const rows = [];
    for (const v of list) {
      const q = await API.post("/api/quote", { ...state.form, type: state.type, vehicle_id: v.id });
      rows.push({ v, q });
    }
    const draw = () => {
      const sort = document.getElementById("sort").value;
      rows.sort((a, b) => sort === "seats" ? (b.v.seats || 0) - (a.v.seats || 0) : a.q.fare.total - b.q.fare.total);
      box.innerHTML = rows.map(({ v, q }) => `<article class="result">
        <img src="${v.img || ""}" alt=""/>
        <div><h3>${RL.car(v)}</h3>
          <p class="sub">${v.seats || "-"} ${RL.t("pax")} · ${v.bags || v.trans || ""} ${v.shared ? "· shuttle" : ""}</p>
          ${q.night ? `<span class="badge">${RL.t("night")}</span>` : ""}
          <p class="meta">${RL.t("cancel")}</p>
        </div>
        <div style="text-align:right">
          ${v.old ? `<div><s>${RL.nt(v.old)}</s></div>` : ""}
          <div class="price">${RL.nt(q.fare.total)}</div>
          ${state.form.roundtrip ? `<div class="meta">×2 ${RL.t("roundtrip")}</div>` : ""}
          <button class="btn btn-k" data-vid="${v.id}">${RL.t("book")}</button>
        </div></article>`).join("");
      box.querySelectorAll("[data-vid]").forEach((b) => b.onclick = () => { state.vehicle = list.find((x) => x.id === b.dataset.vid); show("detail"); });
    };
    document.getElementById("sort").onchange = draw;
    document.getElementById("back").onclick = () => show("home");
    draw();
    return;
  }

  if (view === "detail") {
    const v = state.vehicle;
    const q = await API.post("/api/quote", { ...state.form, type: state.type, vehicle_id: v.id });
    state.quote = q;
    const total = q.fare.total * (state.form.roundtrip ? 2 : 1);
    root.innerHTML = `<div class="wrap two">
      <div>
        <button class="pill" id="back">${RL.t("results")}</button>
        <img src="${v.img || ""}" style="width:100%;height:300px;object-fit:cover;border-radius:16px;margin-top:12px"/>
        <h2>${RL.car(v)}</h2>
        <div class="panel">
          <h3>${RL.t("included")}</h3>
          <p class="sub">${RL.t("meet")} · ${RL.t("flight")} · ${RL.t("cancel")}</p>
          <h3>${RL.t("pay")}</h3>
          <p class="sub">Visa / LINE Pay / Apple Pay · TWD</p>
        </div>
      </div>
      <aside class="bookbox">
        <div class="sub">${RL.loc(place(state.form.from_id))} → ${RL.loc(place(state.form.to_id))}</div>
        <div class="price" style="font-size:28px">${RL.nt(total)}</div>
        <p class="sub">base ${RL.nt(q.fare.base)} · extras ${RL.nt(q.fare.extras)} · night ${RL.nt(q.fare.night)} · promo -${RL.nt(q.fare.discount)}</p>
        <button class="btn btn-k btn-block" id="toPay">${RL.t("book")}</button>
      </aside></div>`;
    document.getElementById("back").onclick = () => show("results");
    document.getElementById("toPay").onclick = () => show("checkout");
    return;
  }

  if (view === "checkout") {
    const v = state.vehicle;
    const total = state.quote.fare.total * (state.form.roundtrip ? 2 : 1);
    root.innerHTML = `<div class="wrap two">
      <form class="panel" id="pay">
        <h2>${RL.t("checkout")}</h2>
        <div class="field">Name / 姓名<input name="name" value="${state.form.name}"/></div>
        <div class="field">Mobile<input name="phone" value="${state.form.phone}"/></div>
        <div class="field">${RL.t("flight")}<input name="flight" value="${state.form.flight}"/></div>
        <div class="field">${RL.t("pay")}
          <select name="pay"><option value="card">Visa / Master</option><option value="line">LINE Pay</option><option value="apple">Apple Pay</option></select>
        </div>
        <button class="btn btn-k" type="submit">${RL.t("pay")} · ${RL.nt(total)}</button>
      </form>
      <aside class="panel"><h3>${RL.car(v)}</h3>
        <p>${RL.loc(place(state.form.from_id))}<br/>→ ${RL.loc(place(state.form.to_id))}</p>
        <p class="price">${RL.nt(total)}</p></aside>
    </div>`;
    document.getElementById("pay").onsubmit = async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      state.booking = await API.post("/api/bookings", {
        ...state.form, type: state.type, vehicle_id: v.id, channel: "web",
        name: fd.get("name"), phone: fd.get("phone"), flight: fd.get("flight"),
      });
      if (state.form.roundtrip) {
        await API.post("/api/bookings", {
          ...state.form, type: state.type === "airport_pickup" ? "airport_drop" : state.type,
          from_id: state.form.to_id, to_id: state.form.from_id,
          vehicle_id: v.id, channel: "web", name: fd.get("name"), phone: fd.get("phone"),
        });
      }
      show("done");
    };
    return;
  }

  if (view === "done") {
    const b = state.booking;
    root.innerHTML = `<div class="ok">
      <h2>${RL.t("confirm")}</h2>
      <p>${b.id} · ${RL.nt(b.fare.total)}</p>
      <div class="voucher">
        <b>${RL.t("voucher")}</b>
        <p>${RL.loc(b.from_place)} → ${RL.loc(b.to_place)}</p>
        <p>${RL.car(b.vehicle)}</p>
        <p>${RL.t("otp")}: <b>${b.otp}</b></p>
        <p>${RL.t("flight")}: ${b.flight || "-"}</p>
      </div>
      <p><button class="btn btn-k" id="toTrips">${RL.t("bookings")}</button></p>
    </div>`;
    document.getElementById("toTrips").onclick = () => show("bookings");
    return;
  }

  if (view === "bookings") {
    const rows = await API.get("/api/bookings");
    const mine = rows.filter((b) => b.channel === "web" || b.channel === "app" || b.channel === "dispatch");
    const f = state.tripFilter;
    const filtered = mine.filter((b) => {
      if (f === "all") return true;
      if (f === "upcoming") return ["new", "assigned", "accepted"].includes(b.status);
      if (f === "live") return ["arriving", "onboard"].includes(b.status);
      return b.status === f;
    });
    root.innerHTML = `<div class="wrap sec">
      <h2>${RL.t("bookings")}</h2>
      <div class="tabs" id="tf">
        ${[["all","all"],["upcoming","upcoming"],["live","live"],["completed","done"],["cancelled","cancelled"]].map(([id,k]) =>
          `<button class="tab ${f===id?"on":""}" data-f="${id}">${RL.t(k)}</button>`).join("")}
      </div>
      ${filtered.map((b) => `<article class="result job-card" style="grid-template-columns:1fr auto">
        <div>
          <span class="st st-${b.status}">${b.status}</span>
          <b> ${b.id}</b> · ${b.channel} · ${b.type}<br/>
          ${RL.loc(b.from_place)} → ${RL.loc(b.to_place)}<br/>
          ${RL.car(b.vehicle)} · OTP ${b.otp}
          ${b.driver ? `<div>${b.driver.name} ${b.driver.plate}</div>` : ""}
          <div class="meta">${(b.timeline || []).map((t) => t.status).join(" → ")}</div>
        </div>
        <div>
          <div class="price">${RL.nt(b.fare.total)}</div>
          ${["new","assigned","accepted"].includes(b.status) ? `<button class="pill" data-cancel="${b.id}">${RL.t("cancelled")}</button>` : ""}
          ${["new","assigned"].includes(b.status) ? `<button class="pill" data-mod="${b.id}">${RL.t("modify")}</button>` : ""}
        </div>
      </article>`).join("") || `<p>${RL.t("noTrips")}</p>`}
    </div>`;
    document.querySelectorAll("[data-f]").forEach((t) => t.onclick = () => { state.tripFilter = t.dataset.f; show("bookings"); });
    document.querySelectorAll("[data-cancel]").forEach((b) => b.onclick = async () => {
      await API.post(`/api/bookings/${b.dataset.cancel}/cancel`, {});
      show("bookings");
    });
    document.querySelectorAll("[data-mod]").forEach((b) => b.onclick = async () => {
      const when = prompt(RL.t("when"), state.form.when);
      if (!when) return;
      await API.post(`/api/bookings/${b.dataset.mod}/modify`, { when, notes: "guest modify" });
      show("bookings");
    });
    return;
  }

  if (view === "wishlist") {
    const w = await API.get("/api/wishlist");
    root.innerHTML = `<div class="wrap sec"><h2>${RL.t("wish")}</h2>
      <div class="grid4">${w.cards.map(liveCard).join("") || `<p>${RL.t("noTrips")}</p>`}</div></div>`;
    root.querySelectorAll("[data-route]").forEach((el) => el.onclick = () => {
      const r = w.cards.find((x) => x.id === el.dataset.route);
      state.form.from_id = r.from; state.form.to_id = r.to; show("results");
    });
    return;
  }

  if (view === "safety") {
    root.innerHTML = `<div class="wrap sec"><h2>${RL.t("safety")}</h2>
      <div class="grid4" style="grid-template-columns:repeat(3,1fr)">
        <div class="panel"><b>${RL.t("shareTrip")}</b><p class="sub">OTP + live driver plate</p></div>
        <div class="panel"><b>SOS</b><p class="sub">Fleet OS 24h · 交通事故 / 車輛故障 / 醫療</p></div>
        <div class="panel"><b>ITRI</b><p class="sub">Rank-aggregation dispatch · OSRM ETA</p></div>
      </div></div>`;
    return;
  }

  if (view === "taxi") {
    state.type = "instant";
    root.innerHTML = `<div class="wrap sec"><h2>${RL.t("taxi")}</h2>
      <div class="search">${searchForm()}</div>
      <div id="taxis" style="margin-top:16px"></div></div>`;
    bindForm(root);
    root.querySelectorAll("[data-type]").forEach((t) => t.onclick = () => { state.type = t.dataset.type; show(t.dataset.type === "instant" ? "taxi" : "home"); });
    document.getElementById("goSearch").onclick = async () => {
      const box = document.getElementById("taxis");
      box.innerHTML = "";
      for (const v of state.catalog.taxi_classes) {
        const q = await API.post("/api/quote", { ...state.form, type: "instant", vehicle_id: v.id });
        box.insertAdjacentHTML("beforeend", `<article class="result job-card" style="grid-template-columns:1fr auto">
          <div><h3>${RL.car(v)}</h3><p class="sub">ETA ${v.eta} min · ${RL.t("liveBoard")}</p></div>
          <div><div class="price">${RL.nt(q.fare.total)}</div>
          <button class="btn btn-k" data-vid="${v.id}">${RL.t("confirmRide")}</button></div></article>`);
      }
      box.querySelectorAll("[data-vid]").forEach((btn) => btn.onclick = async () => {
        state.booking = await API.post("/api/bookings", { ...state.form, type: "instant", vehicle_id: btn.dataset.vid, channel: "web" });
        show("done");
      });
    };
    document.getElementById("goSearch").click();
  }
}

async function boot() {
  document.getElementById("langBtn").onclick = () => RL.toggle();
  document.querySelectorAll("[data-nav]").forEach((a) => {
    a.textContent = RL.t(a.dataset.nav);
    a.onclick = (e) => {
      e.preventDefault();
      show(a.dataset.go);
    };
  });
  state.catalog = await API.get("/api/catalog");
  state.form.when = tomorrow10();
  const hash = (location.hash || "#pickup").replace("#", "") || "pickup";
  show(["results","detail","checkout","done"].includes(hash) ? "pickup" : hash);
}

boot();
