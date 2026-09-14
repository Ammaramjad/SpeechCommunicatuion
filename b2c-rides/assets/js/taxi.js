const pickup = [28.5562, 77.1000];
const drop = [28.6304, 77.2177];
let map, carMarker, selected = "sedan", fareMul = 1;
let driverTimer;

document.getElementById("langBtn").onclick = () => RideLook.toggleLang();

function initMap() {
  map = L.map("map", { zoomControl: false }).setView([28.59, 77.16], 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap",
  }).addTo(map);
  L.marker(pickup).addTo(map).bindPopup("Pickup · IGI Airport T3");
  L.marker(drop).addTo(map).bindPopup("Drop · Connaught Place");
  L.polyline([pickup, drop], { color: "#ff5b00", weight: 4, opacity: 0.85 }).addTo(map);
  carMarker = L.circleMarker(pickup, { radius: 9, color: "#fff", weight: 2, fillColor: "#ff5b00", fillOpacity: 1 }).addTo(map);
}

function sheet(html) {
  document.getElementById("sheet").innerHTML = html;
}

function quoteView() {
  const classes = RIDEDATA.taxiClasses.map((c) => `
    <div class="vopt ${c.id === selected ? "selected" : ""}" data-id="${c.id}">
      <img src="${c.img}" alt="" />
      <div style="flex:1">
        <strong>${c.name}</strong>
        <div class="meta">${c.desc} · ETA ${c.eta}</div>
      </div>
      <strong>${RideLook.inr(Math.round(c.price * fareMul))}</strong>
    </div>
  `).join("");
  sheet(`
    <p class="kicker">Demo B · Instant taxi</p>
    <h2 style="margin:4px 0 10px">${RideLook.t("where")}</h2>
    <div class="field"><label>Pickup</label><input value="IGI Airport T3, Delhi" readonly /></div>
    <div class="field"><label>Drop-off</label><input id="dropInput" value="Connaught Place, Delhi" /></div>
    ${classes}
    <button class="btn btn-orange btn-block" id="confirmRide" type="button">${RideLook.t("confirmRide")} · ${RideLook.inr(priceNow())}</button>
  `);
  document.querySelectorAll(".vopt").forEach((el) => {
    el.onclick = () => { selected = el.dataset.id; quoteView(); };
  });
  document.getElementById("dropInput").oninput = (e) => {
    document.getElementById("pinNote").textContent = "Set drop-off · " + e.target.value;
  };
  document.getElementById("confirmRide").onclick = matchingView;
}

function priceNow() {
  const c = RIDEDATA.taxiClasses.find((x) => x.id === selected);
  return Math.round(c.price * fareMul);
}

function matchingView() {
  sheet(`
    <h2>Finding your ${RIDEDATA.taxiClasses.find((x) => x.id === selected).name}…</h2>
    <p class="meta">Nearby drivers in South-West Delhi</p>
    <div class="btn btn-ghost btn-block" style="pointer-events:none">Matching · ~8 sec</div>
  `);
  setTimeout(driverView, 1800);
}

function driverView() {
  sheet(`
    <div class="driver-row">
      <img class="avatar" alt="Driver" src="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=200&q=60" />
      <div style="flex:1">
        <strong>Rakesh Kumar</strong>
        <div class="stars">★ 4.92 · 3,104 trips</div>
        <div class="meta">DL 1C AB 4291 · White Dzire</div>
      </div>
      <div><strong>OTP 4821</strong></div>
    </div>
    <p class="meta" style="margin-top:12px">Arriving in 4 min · ${RideLook.inr(priceNow())} cash/UPI</p>
    <button class="btn btn-orange btn-block" id="startTrip" type="button">Driver is arriving — start trip</button>
  `);
  document.getElementById("startTrip").onclick = trackView;
}

function lerp(a, b, t) {
  return a + (b - a) * t;
}

function trackView() {
  sheet(`
    <h2>On trip</h2>
    <p class="meta">IGI T3 → Connaught Place</p>
    <p><strong>Share live location with family</strong></p>
    <button class="btn btn-orange btn-block" id="endTrip" type="button">Complete trip (demo)</button>
  `);
  document.getElementById("endTrip").onclick = doneView;
  let t = 0;
  clearInterval(driverTimer);
  driverTimer = setInterval(() => {
    t += 0.02;
    if (t > 1) { clearInterval(driverTimer); t = 1; }
    const lat = lerp(pickup[0], drop[0], t);
    const lng = lerp(pickup[1], drop[1], t);
    carMarker.setLatLng([lat, lng]);
    map.panTo([lat, lng], { animate: true });
  }, 120);
}

function doneView() {
  clearInterval(driverTimer);
  carMarker.setLatLng(drop);
  sheet(`
    <h2>Trip complete</h2>
    <p>You paid ${RideLook.inr(priceNow())} · Rate Rakesh</p>
    <p class="stars" style="font-size:22px">★★★★★</p>
    <a class="btn btn-orange btn-block" href="index.html">Back to demos</a>
  `);
}

initMap();
quoteView();
