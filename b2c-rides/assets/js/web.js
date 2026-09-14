const state = {
  catalog: null,
  type: "airport_pickup",
  quote: null,
  vehicle: null,
  booking: null,
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
    promo: "",
    name: "林小華",
    phone: "0912-000-888",
    flight: "CI 011",
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

function opts(places, selected) {
  return places.map((p) => `<option value="${p.id}" ${p.id === selected ? "selected" : ""}>${RL.loc(p)}</option>`).join("");
}

function extras() {
  const f = state.form;
  return `
    <div class="checks">
      <label><input type="checkbox" data-k="meet" ${f.meet ? "checked" : ""}/> ${RL.t("meet")}</label>
      <label><input type="checkbox" data-k="child_seat" ${f.child_seat ? "checked" : ""}/> ${RL.t("child")}</label>
      <label><input type="checkbox" data-k="english" ${f.english ? "checked" : ""}/> ${RL.t("english")}</label>
      <label><input type="checkbox" data-k="pet" ${f.pet ? "checked" : ""}/> ${RL.t("pet")}</label>
    </div>`;
}

function searchForm() {
  const f = state.form;
  const extraHour = state.type === "hourly" ? `<div class="field">${RL.t("hours")}<input type="number" min="4" max="12" value="${f.hours}" data-k="hours"/></div>` : "";
  const extraDay = state.type === "rental" ? `<div class="field">${RL.t("days")}<input type="number" min="1" max="14" value="${f.days}" data-k="days"/></div>` : "";
  return `
    <div class="tabs" id="typeTabs">
      ${[["airport_pickup", "pickup"],["airport_drop","drop"],["p2p","p2p"],["hourly","hourly"],["rental","rental"],["instant","taxi"]].map(([id,k]) =>
        `<button class="tab ${state.type===id?"on":""}" data-type="${id}" type="button">${RL.t(k)}</button>`).join("")}
    </div>
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
    if (el.tagName === "SELECT") el.value = state.form[el.dataset.k] || el.value;
  });
}

async function show(view, extra) {
  const root = document.getElementById("view");
  if (view === "home") {
    root.innerHTML = `
      <section class="hero"><div class="wrap">
        <h1>${RL.t("hero")}</h1><p>${RL.t("heroSub")}</p>
        <div class="search">${searchForm()}</div>
      </div></section>
      <section class="sec wrap">
        <h2>${RL.t("popular")}</h2>
        <div class="grid4" id="routes"></div>
      </section>
      <section class="sec wrap" style="padding-top:0">
        <h2>${RL.t("why")}</h2>
        <div class="grid4" style="grid-template-columns:repeat(3,1fr)">
          <div class="panel"><b>${RL.t("why1t")}</b><p class="sub">${RL.t("why1")}</p></div>
          <div class="panel"><b>${RL.t("why2t")}</b><p class="sub">${RL.t("why2")}</p></div>
          <div class="panel"><b>${RL.t("why3t")}</b><p class="sub">${RL.t("why3")}</p></div>
        </div>
      </section>`;
    document.getElementById("routes").innerHTML = state.catalog.routes.map((r) => {
      const a = state.catalog.places.find((p) => p.id === r.from);
      const b = state.catalog.places.find((p) => p.id === r.to);
      return `<article class="card" data-route="${r.id}"><img src="${r.img}" alt=""/>
        <div class="pad"><span class="badge">${r.mins} min</span>
        <h3>${RL.loc(a)} → ${RL.loc(b)}</h3>
        <div class="price">${RL.t("fromPrice").replace("{n}", r.from_price.toLocaleString("zh-TW"))}</div></div></article>`;
    }).join("");
    bindForm(root);
    root.querySelectorAll("[data-type]").forEach((t) => t.onclick = () => { state.type = t.dataset.type; show("home"); });
    root.querySelectorAll("[data-route]").forEach((el) => el.onclick = () => {
      const r = state.catalog.routes.find((x) => x.id === el.dataset.route);
      state.form.from_id = r.from; state.form.to_id = r.to; show("results");
    });
    document.getElementById("goSearch").onclick = () => show(state.type === "instant" ? "taxi" : "results");
  }

  if (view === "results") {
    const list = state.type === "rental" ? state.catalog.rentals : state.catalog.vehicles;
    root.innerHTML = `<div class="wrap split">
      <aside class="filters">
        <button class="pill" id="back">${RL.t("home")}</button>
        <h3>${RL.t("results")}</h3>
        <p class="sub">${RL.loc(place(state.form.from_id))} → ${RL.loc(place(state.form.to_id))}</p>
      </aside>
      <div id="list"></div>
    </div>`;
    const box = document.getElementById("list");
    for (const v of list) {
      const q = await API.post("/api/quote", { ...state.form, type: state.type, vehicle_id: v.id });
      box.insertAdjacentHTML("beforeend", `<article class="result">
        <img src="${v.img}" alt=""/>
        <div><h3>${RL.car(v)}</h3>
          <p class="sub">${v.seats || "-"} seats · ${v.bags || v.trans || ""} ${v.shared ? "· shuttle" : ""}</p>
          ${q.night ? `<span class="badge">${RL.t("night")}</span>` : ""}
        </div>
        <div style="text-align:right">
          ${v.old ? `<div><s>${RL.nt(v.old)}</s></div>` : ""}
          <div class="price">${RL.nt(q.fare.total)}</div>
          <button class="btn btn-k" data-vid="${v.id}">${RL.t("book")}</button>
        </div></article>`);
    }
    document.getElementById("back").onclick = () => show("home");
    box.querySelectorAll("[data-vid]").forEach((b) => b.onclick = () => { state.vehicle = list.find((x) => x.id === b.dataset.vid); show("detail"); });
  }

  if (view === "detail") {
    const v = state.vehicle;
    const q = await API.post("/api/quote", { ...state.form, type: state.type, vehicle_id: v.id });
    state.quote = q;
    root.innerHTML = `<div class="wrap two">
      <div>
        <button class="pill" id="back">${RL.t("results")}</button>
        <img src="${v.img}" style="width:100%;height:300px;object-fit:cover;border-radius:16px;margin-top:12px"/>
        <h2>${RL.car(v)}</h2>
        <div class="panel"><h3>${RL.t("included")}</h3>
          <p class="sub">${RL.t("meet")} · ${RL.t("flight")} · GST-style invoice demo · ${RL.t("cancel")}</p></div>
      </div>
      <aside class="bookbox">
        <div class="sub">${RL.loc(place(state.form.from_id))} → ${RL.loc(place(state.form.to_id))}</div>
        <div class="price" style="font-size:28px">${RL.nt(q.fare.total)}</div>
        <p class="sub">base ${RL.nt(q.fare.base)} · extras ${RL.nt(q.fare.extras)} · night ${RL.nt(q.fare.night)} · promo -${RL.nt(q.fare.discount)}</p>
        <button class="btn btn-k btn-block" id="toPay">${RL.t("book")}</button>
      </aside></div>`;
    document.getElementById("back").onclick = () => show("results");
    document.getElementById("toPay").onclick = () => show("checkout");
  }

  if (view === "checkout") {
    const v = state.vehicle;
    root.innerHTML = `<div class="wrap two">
      <form class="panel" id="pay">
        <h2>${RL.t("checkout")}</h2>
        <div class="field">Name / 姓名<input name="name" value="${state.form.name}"/></div>
        <div class="field">Mobile<input name="phone" value="${state.form.phone}"/></div>
        <div class="field">${RL.t("flight")}<input name="flight" value="${state.form.flight}"/></div>
        <div class="field">Card (demo)<input value="4242 ···· ···· 4242"/></div>
        <button class="btn btn-k" type="submit">${RL.t("pay")} · ${RL.nt(state.quote.fare.total)}</button>
      </form>
      <aside class="panel"><h3>${RL.car(v)}</h3>
        <p>${RL.loc(place(state.form.from_id))}<br/>→ ${RL.loc(place(state.form.to_id))}</p>
        <p class="price">${RL.nt(state.quote.fare.total)}</p></aside>
    </div>`;
    document.getElementById("pay").onsubmit = async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      state.booking = await API.post("/api/bookings", {
        ...state.form, type: state.type, vehicle_id: v.id, channel: "web",
        name: fd.get("name"), phone: fd.get("phone"), flight: fd.get("flight"),
      });
      show("done");
    };
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
      <p><a class="btn btn-k" href="#bookings">${RL.t("bookings")}</a></p>
    </div>`;
  }

  if (view === "bookings") {
    const rows = await API.get("/api/bookings");
    root.innerHTML = `<div class="wrap sec"><h2>${RL.t("bookings")}</h2>
      ${rows.map((b) => `<div class="result" style="grid-template-columns:1fr auto">
        <div><b>${b.id}</b> · ${b.channel} · ${b.status}<br/>
        ${RL.loc(b.from_place)} → ${RL.loc(b.to_place)}<br/>${RL.car(b.vehicle)}</div>
        <div class="price">${RL.nt(b.fare.total)}</div></div>`).join("") || "<p>No bookings yet</p>"}
    </div>`;
  }

  if (view === "taxi") {
    root.innerHTML = `<div class="wrap sec"><h2>${RL.t("taxi")}</h2>
      <p class="sub">${RL.t("where")} · ${RL.loc(place(state.form.from_id))} → ${RL.loc(place(state.form.to_id))}</p>
      <div id="taxis"></div></div>`;
    const box = document.getElementById("taxis");
    for (const v of state.catalog.taxi_classes) {
      const q = await API.post("/api/quote", { ...state.form, type: "instant", vehicle_id: v.id });
      box.insertAdjacentHTML("beforeend", `<article class="result" style="grid-template-columns:1fr auto">
        <div><h3>${RL.car(v)}</h3><p class="sub">ETA ${v.eta} min</p></div>
        <div><div class="price">${RL.nt(q.fare.total)}</div>
        <button class="btn btn-k" data-vid="${v.id}">${RL.t("confirmRide")}</button></div></article>`);
    }
    box.querySelectorAll("[data-vid]").forEach((btn) => btn.onclick = async () => {
      state.booking = await API.post("/api/bookings", { ...state.form, type: "instant", vehicle_id: btn.dataset.vid, channel: "web" });
      show("done");
    });
  }
}

function place(id) {
  return state.catalog.places.find((p) => p.id === id);
}

async function boot() {
  document.getElementById("langBtn").onclick = () => RL.toggle();
  document.querySelectorAll("[data-nav]").forEach((a) => {
    a.textContent = RL.t(a.dataset.nav);
    a.onclick = (e) => { e.preventDefault(); show(a.dataset.go); };
  });
  state.catalog = await API.get("/api/catalog");
  state.form.when = tomorrow10();
  const hash = location.hash.replace("#", "");
  show(hash === "bookings" ? "bookings" : "home");
  window.addEventListener("hashchange", () => {
    if (location.hash === "#bookings") show("bookings");
  });
}

boot();
