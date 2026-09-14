let catalog, map, markers = [];

function stClass(s) { return "st st-" + s; }

async function refresh() {
  const sum = await API.get("/api/fleet/summary");
  const jobs = await API.get("/api/bookings");
  const drivers = await API.get("/api/drivers");
  document.getElementById("kpis").innerHTML = `
    <div class="kpi"><span>${RL.t("jobs")}</span><b>${sum.active_jobs}</b></div>
    <div class="kpi"><span>${RL.t("available")}</span><b>${sum.available_drivers}</b></div>
    <div class="kpi"><span>${RL.t("gmv")}</span><b>${RL.nt(sum.gmv)}</b></div>
    <div class="kpi"><span>Web / App / Phone</span><b>${sum.channels.web} / ${sum.channels.app} / ${sum.channels.dispatch}</b></div>`;
  document.getElementById("jobs").innerHTML = jobs.map((b) => `
    <div class="job">
      <div>
        <span class="${stClass(b.status)}">${b.status}</span>
        <b> ${b.id}</b> · ${b.channel} · ${b.type}<br/>
        ${RL.loc(b.from_place)} → ${RL.loc(b.to_place)}<br/>
        ${RL.car(b.vehicle)} · ${RL.nt(b.fare.total)} · OTP ${b.otp}
        ${b.driver ? `<div>司機 ${b.driver.name} ${b.driver.plate}</div>` : ""}
      </div>
      <div>
        ${b.status === "new" ? `<select data-assign="${b.id}">${drivers.filter(d=>d.status==='available').map(d=>`<option value="${d.id}">${d.name}</option>`).join("")}</select>
        <button class="btn btn-k" data-do="assign" data-id="${b.id}">${RL.t("assign")}</button>` : ""}
        ${b.status === "assigned" ? `<button class="pill" data-do="status" data-id="${b.id}" data-s="accepted">${RL.t("accept")}</button>` : ""}
        ${["accepted","arriving","onboard"].includes(b.status) ? `<button class="btn btn-k" data-do="status" data-id="${b.id}" data-s="completed">${RL.t("complete")}</button>` : ""}
      </div>
    </div>`).join("") || "<p>No jobs</p>";

  document.getElementById("drivers").innerHTML = drivers.map((d) => `
    <div class="job"><div><b>${d.name}</b> · ${d.plate}<br/>${d.status} · ★ ${d.rating} · ${d.lang.join(", ")}</div>
    <button class="pill" data-toggle="${d.id}">${d.status === "offline" ? RL.t("online") : RL.t("offline")}</button></div>`).join("");

  document.getElementById("alerts").innerHTML = (sum.alerts || []).slice().reverse().map((a) => `<div class="sub">${a.level}: ${a.message}</div>`).join("");

  if (map) {
    markers.forEach((m) => map.removeLayer(m));
    markers = [];
    drivers.forEach((d) => {
      const m = L.circleMarker([d.lat, d.lng], { radius: 8, color: d.status === "available" ? "#6ee7a8" : d.status === "busy" ? "#ff5b00" : "#64748b", fillOpacity: 1 })
        .addTo(map).bindPopup(`${d.name}<br/>${d.plate}<br/>${d.status}`);
      markers.push(m);
    });
    jobs.filter((b) => !["completed","cancelled"].includes(b.status)).forEach((b) => {
      const p = b.from_place;
      if (p && p.lat) {
        const m = L.marker([p.lat, p.lng]).addTo(map).bindPopup(b.id);
        markers.push(m);
      }
    });
  }

  document.querySelectorAll("[data-do='assign']").forEach((btn) => btn.onclick = async () => {
    const sel = document.querySelector(`[data-assign="${btn.dataset.id}"]`);
    if (!sel || !sel.value) return;
    await API.post(`/api/bookings/${btn.dataset.id}/assign`, { driver_id: sel.value });
    refresh();
  });
  document.querySelectorAll("[data-do='status']").forEach((btn) => btn.onclick = async () => {
    await API.post(`/api/bookings/${btn.dataset.id}/status`, { status: btn.dataset.s });
    refresh();
  });
  document.querySelectorAll("[data-toggle]").forEach((btn) => btn.onclick = async () => {
    await API.post(`/api/drivers/${btn.dataset.toggle}/toggle`, {});
    refresh();
  });
}

async function phoneBook(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  await API.post("/api/bookings", {
    channel: "dispatch",
    type: fd.get("type"),
    from_id: fd.get("from_id"),
    to_id: fd.get("to_id"),
    when: fd.get("when"),
    pax: Number(fd.get("pax")),
    vehicle_id: fd.get("vehicle_id"),
    name: fd.get("name"),
    phone: fd.get("phone"),
    flight: fd.get("flight"),
    meet: true,
  });
  e.target.reset();
  refresh();
}

async function boot() {
  catalog = await API.get("/api/catalog");
  document.getElementById("langBtn").onclick = () => RL.toggle();
  document.getElementById("reset").onclick = async () => { await API.post("/api/demo/reset", {}); refresh(); };
  const sel = (name, rows, lab) => `<select name="${name}">${rows.map((p)=>`<option value="${p.id}">${lab(p)}</option>`).join("")}</select>`;
  document.getElementById("phoneForm").innerHTML = `
    <h3>${RL.t("phoneBook")}</h3>
    <select name="type"><option value="airport_pickup">接機</option><option value="airport_drop">送機</option><option value="instant">立即叫車</option><option value="hourly">包車</option></select>
    ${sel("from_id", catalog.places, RL.loc)}
    ${sel("to_id", catalog.places, RL.loc)}
    <input name="when" type="datetime-local" required />
    <input name="pax" type="number" value="2"/>
    ${sel("vehicle_id", catalog.vehicles, RL.car)}
    <input name="name" placeholder="旅客" value="陳先生"/>
    <input name="phone" value="0988-123-456"/>
    <input name="flight" value="CI 160"/>
    <button class="btn btn-k" type="submit">${RL.t("phoneBook")}</button>`;
  document.getElementById("phoneForm").onsubmit = phoneBook;
  map = L.map("fmap").setView([25.04, 121.52], 9);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OSM" }).addTo(map);
  refresh();
  setInterval(refresh, 4000);
}
boot();
