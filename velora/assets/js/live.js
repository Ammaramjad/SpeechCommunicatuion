function icon(name) {
  const paths = {
    home: "M4 12 L12 4 L20 12 V20 H14 V14 H10 V20 H4 Z",
    search: "M11 11 m-7 0 a7 7 0 1 0 14 0 a7 7 0 1 0 -14 0 M16 16 L21 21",
    map: "M4 6 L10 4 L16 6 L22 4 V18 L16 20 L10 18 L4 20 Z",
    trips: "M6 6 H18 V18 H6 Z M8 10 H16 M8 14 H14",
    me: "M12 12 m-4 0 a4 4 0 1 0 8 0 a4 4 0 1 0 -8 0 M6 20 C6 16 9 15 12 15 C15 15 18 16 18 20",
  };
  return `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">${paths[name] ? `<path d="${paths[name]}"/>` : ""}</svg>`;
}

function stars(n) {
  const v = Math.round(Number(n) || 0);
  return "★★★★★".slice(0, v) + "☆☆☆☆☆".slice(0, 5 - v);
}

async function ops(id, kind, extra) {
  return VELORA.post("/api/bookings/" + encodeURIComponent(id) + "/ops", { kind, ...(extra || {}) });
}

function renderAlerts(b) {
  const rows = (b.live && b.live.alerts) || b.alerts || [];
  if (!rows.length) return "";
  return `<div class="alert-list">${rows.slice(0, 5).map((a) => `<div>${a.text}</div>`).join("")}</div>`;
}

function renderComments(b) {
  const rows = (b.driver && b.driver.reviews) || (b.live && b.live.comments) || [];
  if (!rows.length) return `<p class="comment">No verified comments yet.</p>`;
  return rows.map((c) => `<div class="comment"><b>${stars(c.stars)} ${c.name}</b> — ${c.text}</div>`).join("");
}

function driverBlock(b) {
  if (!b.driver) {
    return `<div class="ios-card"><h3>Finding your chauffeur</h3><p class="sub-ios" style="margin:0">You can book before a named driver is assigned.</p></div>`;
  }
  const d = b.driver;
  return `
    <div class="driver-hero">
      <img src="${d.photo}" alt=""/>
      <div>
        <div class="pill">${d.first} · on trip</div>
        <h3 style="margin:6px 0 0">${d.first}</h3>
        <div class="stars">${stars(d.rating)} ${d.rating} · ${(d.trips || 0).toLocaleString()} trips</div>
        <p class="comment" style="margin:4px 0 0">${d.model || ""} · ${d.color || ""} · ${d.plate || ""}</p>
        <p class="comment">${(d.lang || []).join(" · ")}</p>
      </div>
      <div class="eta-num">${b.live ? b.live.eta_min : "—"}</div>
    </div>`;
}

function actionGrid(id) {
  return `
    <div class="ios-row" style="margin-top:12px">
      <button class="ios-btn gray" data-ops="passenger_late">I’m late</button>
      <button class="ios-btn gray" data-ops="driver_late">Driver late</button>
    </div>
    <div class="ios-row" style="margin-top:8px">
      <button class="ios-btn gray" data-ops="flight_sync">Sync flight</button>
      <button class="ios-btn gray" data-ops="change_driver">New driver</button>
    </div>
    <div class="ios-row" style="margin-top:8px">
      <button class="ios-btn danger" data-ops="incident">Accident / replace car</button>
    </div>
    <div class="ios-row" style="margin-top:8px">
      <a class="ios-btn gray" style="text-align:center" href="tel:+886910000111">Call</a>
      <button class="ios-btn gray" id="msgBtn">Message</button>
    </div>`;
}

function bindOps(root, id, after) {
  root.querySelectorAll("[data-ops]").forEach((btn) => {
    btn.onclick = async () => {
      btn.disabled = true;
      try {
        const extra = btn.dataset.ops === "message" ? { note: prompt("Message to driver") || "On my way" } : {};
        await ops(id, btn.dataset.ops, extra);
        if (after) after();
      } catch (e) {
        alert("Could not update trip. Try again.");
      }
      btn.disabled = false;
    };
  });
  const msg = root.querySelector("#msgBtn");
  if (msg) msg.onclick = async () => {
    const note = prompt("Message to driver", "Please call when you arrive.");
    if (note) { await ops(id, "message", { note }); if (after) after(); }
  };
}

function paintMap(map, b) {
  const live = b.live;
  if (!live || !window.L) return;
  map.eachLayer((ly) => { if (ly instanceof L.TileLayer) return; map.removeLayer(ly); });
  const pts = live.route.map((p) => [p.lat, p.lng]);
  L.polyline(pts, { color: "#0071e3", weight: 5, opacity: .85 }).addTo(map);
  L.marker([live.pickup.lat, live.pickup.lng]).addTo(map).bindPopup("Pickup");
  L.marker([live.dest.lat, live.dest.lng]).addTo(map).bindPopup("Drop-off");
  const car = L.circleMarker([live.driver_pos.lat, live.driver_pos.lng], { radius: 9, color: "#1d1d1f", fillColor: "#32d74b", fillOpacity: 1 }).addTo(map);
  car.bindPopup("Driver");
  map.fitBounds(pts, { padding: [28, 28] });
}

function reviewForm(id) {
  return `<div class="ios-card" id="revBox">
    <h3>Rate this ride</h3>
    <div class="field-ios">Stars 1–5 <input id="rvStars" type="number" min="1" max="5" value="5"/></div>
    <div class="field-ios">Comment <textarea id="rvText" placeholder="Punctuality, cleanliness, safety"></textarea></div>
    <button class="ios-btn blue" id="rvSend">Post verified review</button>
  </div>`;
}

window.VELORA_LIVE = { icon, stars, ops, renderAlerts, renderComments, driverBlock, actionGrid, bindOps, paintMap, reviewForm };
