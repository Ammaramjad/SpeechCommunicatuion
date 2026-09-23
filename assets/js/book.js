document.getElementById("chrome-header").innerHTML = headerHTML();
document.getElementById("chrome-footer").innerHTML = footerHTML();
bindChrome();

const API_V1 = (VELORA.apiBase || "") + "/api/v1";
const q = Object.fromEntries(new URLSearchParams(location.search));

const state = {
  step: 1,
  service: q.service || "airport",
  pickup_id: q.pickup_id || "tpe",
  dest_id: q.dest_id || "taipei-101",
  when: q.when || defaultWhen(),
  pax: Number(q.pax || 2),
  bags: Number(q.bags || 2),
  hours: Number(q.hours || 8),
  roundtrip: q.roundtrip === "true",
  currency: VELORA.currency,
  class_id: q.class_id || "",
  extras: [],
  stops: [],
  promo: "",
  flight: q.flight || "",
  track_flight: true,
  first: "", last: "", email: "", phone: "", notes: "",
  searchResults: [],
  quote: null,
};

let catalog = { locations: [], extras: [] };

function defaultWhen() {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  d.setHours(10, 0, 0, 0);
  return d.toISOString().slice(0, 16);
}

async function v1get(path) {
  const r = await fetch(API_V1 + path, { headers: VELORA.headers() });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

async function v1post(path, body) {
  const r = await fetch(API_V1 + path, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...VELORA.headers() },
    body: JSON.stringify(body || {}),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

function setStep(n) {
  state.step = n;
  [1, 2, 3].forEach((i) => {
    document.getElementById("panel" + i).classList.toggle("hidden", i !== n);
    document.querySelector(`.step-dot[data-step="${i}"]`)?.classList.toggle("on", i <= n);
  });
  const labels = ["Trip details", "Choose vehicle", "Passenger & pay"];
  document.getElementById("stepLabel").textContent = labels[n - 1];
}

function locName(id) {
  const row = catalog.locations.find((l) => l.id === id);
  return row ? row.name : id;
}

function renderSummary() {
  const q = state.quote;
  const el = document.getElementById("summary");
  if (!q) {
    el.innerHTML = "<h3>Your trip</h3><p class=\"sub\">Select a vehicle to see pricing.</p>";
    return;
  }
  el.innerHTML = `
    <h3>Price breakdown</h3>
    <p class="sub">${locName(state.pickup_id)} → ${locName(state.dest_id)}</p>
    ${Object.entries(q.breakdown).filter(([k]) => !["total", "tolls", "parking"].includes(k)).map(([k, v]) =>
      `<div class="row-between"><span>${k.replace(/_/g, " ")}</span><b>${q.symbol}${Number(v).toLocaleString()}</b></div>`
    ).join("")}
    <p class="xl">${q.symbol}${Number(q.breakdown.total).toLocaleString()}</p>
    <p class="sub">Total per vehicle · ${q.currency}</p>`;
}

function renderStep1() {
  document.getElementById("panel1").innerHTML = `
    <h2>Where & when</h2>
    <div class="field"><label>Service</label>
      <select id="service">
        <option value="airport">Airport transfer</option>
        <option value="p2p">City transfer</option>
        <option value="hourly">Hourly / charter</option>
      </select>
    </div>
    <div class="field"><label>Pickup</label>
      <select id="pickup">${catalog.locations.map((l) => `<option value="${l.id}">${l.name}</option>`).join("")}</select>
    </div>
    <div class="field"><label>Destination</label>
      <select id="dest">${catalog.locations.map((l) => `<option value="${l.id}">${l.name}</option>`).join("")}</select>
    </div>
    <div class="field"><label>Date & time</label><input id="when" type="datetime-local"/></div>
    <div class="grid-2">
      <div class="field"><label>Passengers</label><input id="pax" type="number" min="1" max="14"/></div>
      <div class="field"><label>Luggage</label><input id="bags" type="number" min="0" max="14"/></div>
    </div>
    <div class="field hourly-only hidden"><label>Hours</label><input id="hours" type="number" min="4" max="12"/></div>
    <div class="field airport-only"><label>Flight number</label><input id="flight" placeholder="CI 011"/></div>
    <label class="airport-only"><input type="checkbox" id="track_flight" checked/> Track flight for pickup</label>
    <p><button class="btn btn-p btn-block sticky-cta" id="toStep2">See vehicles & prices</button></p>`;
  document.getElementById("service").value = state.service;
  document.getElementById("pickup").value = state.pickup_id;
  document.getElementById("dest").value = state.dest_id;
  document.getElementById("when").value = state.when;
  document.getElementById("pax").value = state.pax;
  document.getElementById("bags").value = state.bags;
  document.getElementById("hours")?.value = state.hours;
  document.getElementById("flight").value = state.flight;
  toggleServiceFields();
  document.getElementById("service").onchange = toggleServiceFields;
  document.getElementById("toStep2").onclick = async () => {
    readStep1();
    try {
      const res = await v1post("/pricing/search", payload());
      state.searchResults = res.results || [];
      if (!state.searchResults.length) {
        alert("No vehicles match your passenger/luggage count. Try fewer bags or more passengers filter.");
        return;
      }
      if (!state.class_id) state.class_id = state.searchResults[0].class.id;
      await loadQuote();
      renderStep2();
      setStep(2);
      renderSummary();
    } catch (e) {
      alert(e.message || "Search failed");
    }
  };
}

function toggleServiceFields() {
  const svc = document.getElementById("service").value;
  document.querySelectorAll(".hourly-only").forEach((el) => el.classList.toggle("hidden", svc !== "hourly"));
  document.querySelectorAll(".airport-only").forEach((el) => el.classList.toggle("hidden", svc !== "airport"));
}

function readStep1() {
  state.service = document.getElementById("service").value;
  state.pickup_id = document.getElementById("pickup").value;
  state.dest_id = document.getElementById("dest").value;
  state.when = document.getElementById("when").value;
  state.pax = Number(document.getElementById("pax").value);
  state.bags = Number(document.getElementById("bags").value);
  state.hours = Number(document.getElementById("hours")?.value || 8);
  state.flight = document.getElementById("flight")?.value || "";
  state.track_flight = document.getElementById("track_flight")?.checked || false;
}

function payload() {
  return {
    service: state.service,
    pickup_id: state.pickup_id,
    dest_id: state.dest_id,
    when: state.when,
    pax: state.pax,
    bags: state.bags,
    hours: state.hours,
    roundtrip: state.roundtrip,
    currency: state.currency,
    class_id: state.class_id || "standard",
    promo: state.promo,
    extras: state.extras,
    stops: state.stops,
  };
}

async function loadQuote() {
  state.quote = await v1post("/pricing/quote", payload());
}

function renderStep2() {
  document.getElementById("panel2").innerHTML = `
    <h2>Choose your vehicle</h2>
    <p class="sub">${state.searchResults.length} classes available for ${state.pax} pax · ${state.bags} bags</p>
    <div class="vehicle-list" id="vehicleList"></div>
    <h3>Optional extras</h3>
    <div id="extrasList">${catalog.extras.map((e) =>
      `<label class="check-row"><input type="checkbox" data-ex="${e.id}" ${state.extras.includes(e.id) ? "checked" : ""}/> ${e.name} · ${VELORA.money(e.price, "TWD")}</label>`
    ).join("")}</div>
    <p><button class="btn btn-p btn-block" id="toStep3">Continue</button></p>
    <p><button class="btn btn-g" type="button" id="back1">Back</button></p>`;
  const list = document.getElementById("vehicleList");
  list.innerHTML = state.searchResults.map((row) => {
    const c = row.class;
    const p = row.price;
    const sel = c.id === state.class_id;
    return `<article class="vehicle-card ${sel ? "selected" : ""}" data-id="${c.id}">
      <img src="${c.img || ""}" alt=""/>
      <div>
        <h3>${c.name}</h3>
        <p class="sub">${c.pax} pax · ${c.bags} bags</p>
        <p class="price">${p.symbol}${Number(p.breakdown.total).toLocaleString()}</p>
      </div>
      <button class="btn btn-p" type="button" data-pick="${c.id}">${sel ? "Selected" : "Select"}</button>
    </article>`;
  }).join("");
  list.querySelectorAll("[data-pick]").forEach((btn) => {
    btn.onclick = async () => {
      state.class_id = btn.dataset.pick;
      await loadQuote();
      renderStep2();
      renderSummary();
    };
  });
  document.querySelectorAll("[data-ex]").forEach((c) => {
    c.onchange = async () => {
      state.extras = [...document.querySelectorAll("[data-ex]:checked")].map((x) => x.dataset.ex);
      await loadQuote();
      renderSummary();
    };
  });
  document.getElementById("toStep3").onclick = () => { renderStep3(); setStep(3); };
  document.getElementById("back1").onclick = () => setStep(1);
}

function renderStep3() {
  document.getElementById("panel3").innerHTML = `
    <h2>Passenger & payment</h2>
    <div class="field"><label>First name</label><input id="first" required/></div>
    <div class="field"><label>Last name</label><input id="last" required/></div>
    <div class="field"><label>Email</label><input id="email" type="email" required/></div>
    <div class="field"><label>Phone</label><input id="phone" required/></div>
    <div class="field"><label>Special instructions</label><textarea id="notes"></textarea></div>
    <div class="field"><label>Payment</label>
      <select id="payMethod"><option value="card">Card</option><option value="apple">Apple Pay</option><option value="google">Google Pay</option></select>
    </div>
    <label><input type="checkbox" id="terms" checked/> ${VELORA.t("terms")}</label>
    <p><button class="btn btn-p btn-block sticky-cta" id="payBtn">${VELORA.t("confirm")}</button></p>
    <p class="sub err" id="err"></p>
    <p><button class="btn btn-g" type="button" id="back2">Back</button></p>`;
  if (VELORA.user) {
    document.getElementById("first").value = VELORA.user.name?.split(" ")[0] || "";
    document.getElementById("last").value = VELORA.user.name?.split(" ").slice(1).join(" ") || "";
    document.getElementById("email").value = VELORA.user.email || "";
  }
  document.getElementById("back2").onclick = () => setStep(2);
  document.getElementById("payBtn").onclick = submitBooking;
}

async function submitBooking() {
  const err = document.getElementById("err");
  err.textContent = "";
  if (!document.getElementById("terms").checked) {
    err.textContent = "Please accept terms.";
    return;
  }
  const body = {
    ...payload(),
    first: document.getElementById("first").value.trim(),
    last: document.getElementById("last").value.trim(),
    email: document.getElementById("email").value.trim(),
    phone: document.getElementById("phone").value.trim(),
    flight: state.flight,
    track_flight: state.track_flight,
    notes: document.getElementById("notes").value,
    channel: "web",
    payment_method: document.getElementById("payMethod").value,
    idempotency_key: "book-" + Date.now(),
  };
  try {
    const booking = await v1post("/bookings", body);
    VELORA.track("booking_confirmed_v1", { ref: booking.reference });
    location.href = VELORA.url(`confirm.html?ref=${encodeURIComponent(booking.reference)}&v1=1`);
  } catch (e) {
    err.textContent = e.message || "Booking failed";
  }
}

async function boot() {
  catalog = await VELORA.get("/api/catalog");
  renderStep1();
  setStep(1);
  renderSummary();
}

boot().catch((e) => {
  document.getElementById("panel1").innerHTML = `<p class="err">Unable to load booking: ${e.message}. Start the API server with <code>python3 server.py</code>.</p>`;
});
