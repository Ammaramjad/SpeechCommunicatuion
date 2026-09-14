const LIV = window.VELORA_LIVE;
let tab = "home";
let catalog;
let map;
let liveTimer;
let activeId = localStorage.getItem("vl-live") || "";

function tabs() {
  const items = [
    ["home", "home", "Home"],
    ["book", "search", "Book"],
    ["live", "map", "Live"],
    ["trips", "trips", "Trips"],
    ["me", "me", "Me"],
  ];
  document.getElementById("tabs").innerHTML = items.map(([id, ic, label]) =>
    `<button data-tab="${id}" class="${tab===id?"on":""}">${LIV.icon(ic)}<span>${label}</span></button>`
  ).join("");
  document.querySelectorAll("#tabs button").forEach((b) => b.onclick = () => {
    tab = b.dataset.tab;
    render();
  });
}

function island(text) {
  const el = document.getElementById("island");
  if (text) {
    el.className = "island live";
    el.innerHTML = `<span class="dot"></span><span>${text}</span>`;
  } else {
    el.className = "island";
    el.innerHTML = "";
  }
}

async function render() {
  tabs();
  const el = document.getElementById("body");
  el.className = "ios-body";
  if (liveTimer) { clearInterval(liveTimer); liveTimer = null; }
  if (tab === "home") {
    island("");
    el.innerHTML = `
      <p class="sub-ios" style="margin-top:56px">VELORA</p>
      <h1 class="large-title">A private car,<br/>on your time.</h1>
      <p class="sub-ios">Airport, city, and hourly — booked on web or in this app, same trip.</p>
      <div class="ios-card">
        <h3>Where to?</h3>
        <p class="comment">TPE · Taipei 101 · hotels on file</p>
        <button class="ios-btn blue" id="goBook">Book a ride</button>
      </div>
      <div class="ios-card">
        <h3>Live trip</h3>
        <p class="comment">${activeId ? "Open tracking for " + activeId : "After booking, the map and driver live here."}</p>
        <button class="ios-btn gray" id="goLive">${activeId ? "Open live map" : "No active trip"}</button>
      </div>`;
    document.getElementById("goBook").onclick = () => { tab = "book"; render(); };
    document.getElementById("goLive").onclick = () => { tab = "live"; render(); };
  }
  if (tab === "book") {
    island("");
    el.innerHTML = `
      <h1 class="large-title">Book</h1>
      <p class="sub-ios">Prices match the website. Guest checkout is allowed.</p>
      <div class="ios-card">
        <div class="field-ios">Pickup
          <select id="p">${catalog.locations.map((l) => `<option value="${l.id}">${l.name}</option>`).join("")}</select>
        </div>
        <div class="field-ios">Drop-off
          <select id="d">${catalog.locations.map((l) => `<option value="${l.id}" ${l.id==="taipei-101"?"selected":""}>${l.name}</option>`).join("")}</select>
        </div>
        <div class="field-ios">When <input id="when" type="datetime-local" value="${tomorrow()}"/></div>
        <div class="ios-row">
          <div class="field-ios" style="flex:1">Passengers <input id="pax" type="number" value="2" min="1"/></div>
          <div class="field-ios" style="flex:1">Bags <input id="bags" type="number" value="2" min="0"/></div>
        </div>
        <div class="field-ios">Flight <input id="flight" placeholder="CI 011" value="CI 011"/></div>
        <button class="ios-btn blue" id="see">See cars</button>
      </div>
      <div id="cars"></div>`;
    document.getElementById("see").onclick = loadCars;
  }
  if (tab === "live") await showLive(el);
  if (tab === "trips") {
    island("");
    const rows = await VELORA.get("/api/bookings").catch(() => []);
    el.innerHTML = `<h1 class="large-title">Trips</h1>` + (rows.map((b) => `
      <div class="ios-card">
        <p class="comment">${(b.status || "").replace(/_/g, " ")}</p>
        <h3>${b.id}</h3>
        <p class="comment">${b.pickup.name}<br/>→ ${b.dest.name}</p>
        <p class="comment">${b.channel || "web"} · ${b.quote.symbol}${b.quote.breakdown.total.toLocaleString()}</p>
        <button class="ios-btn gray" data-open="${b.id}">Live map</button>
      </div>`).join("") || `<div class="ios-card">No trips yet. Book from this app or the website.</div>`);
    el.querySelectorAll("[data-open]").forEach((b) => b.onclick = () => {
      activeId = b.dataset.open;
      localStorage.setItem("vl-live", activeId);
      tab = "live";
      render();
    });
  }
  if (tab === "me") {
    island("");
    el.innerHTML = `
      <h1 class="large-title">You</h1>
      <div class="ios-card">
        <h3>Same account as the site</h3>
        <p class="comment">${VELORA.user ? VELORA.user.email : "Guest · bookings still work"}</p>
        <a class="ios-btn blue" href="/account.html" style="display:block;text-align:center">Sign in on web</a>
      </div>
      <div class="ios-card">
        <h3>Also coming</h3>
        <p class="comment">Share live ETA, Family profiles, Apple Pay on-device, Lost-and-found locker, and in-app SOS — architecture is ready.</p>
      </div>`;
  }
}

async function loadCars() {
  const pickup_id = document.getElementById("p").value;
  const dest_id = document.getElementById("d").value;
  const res = await VELORA.post("/api/search", {
    pickup_id, dest_id, when: document.getElementById("when").value, pax: Number(pax.value), bags: Number(bags.value), currency: VELORA.currency, service: "airport",
  });
  document.getElementById("cars").innerHTML = res.results.slice(0, 6).map((r) => `
    <div class="ios-card">
      <h3>${r.class.name}</h3>
      <p class="comment">${r.class.example} · ★ ${r.operator.rating}</p>
      <p class="stars" style="color:#1d1d1f;font-size:22px">${r.price.symbol}${r.price.breakdown.total.toLocaleString()}</p>
      <button class="ios-btn blue" data-c="${r.class.id}">Confirm ride</button>
    </div>`).join("");
  document.querySelectorAll("[data-c]").forEach((btn) => btn.onclick = () => book(btn.dataset.c));
}

async function book(class_id) {
  const body = {
    pickup_id: document.getElementById("p").value,
    dest_id: document.getElementById("d").value,
    when: document.getElementById("when").value,
    pax: Number(document.getElementById("pax").value),
    bags: Number(document.getElementById("bags").value),
    flight: document.getElementById("flight").value,
    track_flight: true,
    class_id,
    first: "Emma", last: "Chen", email: "emma@velora.demo", phone: "+886910000111",
    terms: true, payment: "apple", channel: "app", extras: ["meet"],
  };
  const b = await VELORA.post("/api/bookings", body);
  activeId = b.id;
  localStorage.setItem("vl-live", b.id);
  tab = "live";
  render();
}

async function showLive(el) {
  if (!activeId) {
    const rows = await VELORA.get("/api/bookings").catch(() => []);
    activeId = rows[0] && rows[0].id;
    if (activeId) localStorage.setItem("vl-live", activeId);
  }
  if (!activeId) {
    el.innerHTML = `<h1 class="large-title">Live</h1><div class="ios-card">Book a ride to see the driver on the map.</div>`;
    return;
  }
  el.className = "ios-body map-mode";
  el.innerHTML = `<div id="amap" class="hero-map"></div><div class="sheet" id="sheet"></div>`;
  map = L.map("amap", { zoomControl: false, attributionControl: false }).setView([25.04, 121.5], 11);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18 }).addTo(map);
  const tick = async () => {
    const b = await VELORA.get("/api/bookings/" + encodeURIComponent(activeId) + "/live");
    island(b.live.headline.slice(0, 28));
    LIV.paintMap(map, b);
    const fl = b.live.flight;
    document.getElementById("sheet").innerHTML = `
      <div class="handle"></div>
      <p class="pill">${b.live.headline}</p>
      <h2 style="margin:8px 0 12px">${b.pickup.name.split("(")[0]} → ${b.dest.name.split("/")[0]}</h2>
      ${LIV.driverBlock(b)}
      ${fl ? `<p class="${fl.delay_min ? "pill warn" : "pill"}" style="margin-top:10px">Flight ${fl.code} · ${fl.delay_min ? fl.delay_min + " min late" : "on time"} · wait ${b.live.wait_min} min</p>` : ""}
      ${b.live.incident ? `<p class="pill red">Incident · replacement ${b.live.replacement ? b.live.replacement.first : "sourcing"}</p>` : ""}
      ${LIV.renderAlerts(b)}
      <p class="comment">OTP ${b.otp} · ${b.live.km} km · pickup ${b.live.expected_pickup}</p>
      ${LIV.actionGrid(b.id)}
      <h3 style="margin:16px 0 4px">Verified comments</h3>
      ${LIV.renderComments(b)}
      ${LIV.reviewForm(b.id)}`;
    LIV.bindOps(document.getElementById("sheet"), b.id, tick);
    const send = document.getElementById("rvSend");
    if (send) send.onclick = async () => {
      await VELORA.post("/api/bookings/" + b.id + "/review", { driver: Number(rvStars.value), text: rvText.value, name: "App user" });
      tick();
    };
  };
  await tick();
  liveTimer = setInterval(tick, 4000);
  setTimeout(() => map.invalidateSize(), 250);
}

async function boot() {
  catalog = await VELORA.get("/api/catalog");
  const qid = new URLSearchParams(location.search).get("id");
  if (qid) { activeId = qid; localStorage.setItem("vl-live", qid); tab = "live"; }
  render();
}
boot();
