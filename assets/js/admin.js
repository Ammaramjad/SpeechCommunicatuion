const FLEET = "https://fleet-dispatch-demo-8c37.surge.sh/";
let view = "dash";
let catalog;

function alertHtml(b) {
  const rows = b.alerts || (b.live && b.live.alerts) || [];
  if (!rows.length) return "";
  return `<div class="alert-list">${rows.slice(0, 3).map((a) => `<div>${a.text}</div>`).join("")}</div>`;
}

async function paint() {
  const panel = document.getElementById("panel");
  if (view === "dash") {
    const m = await VELORA.get("/api/admin/metrics");
    panel.innerHTML = `<h1>Today</h1>
      <div class="kpis">
        <div class="kpi">Bookings <b>${m.bookings}</b></div>
        <div class="kpi">Pending <b>${m.pending}</b></div>
        <div class="kpi">Active rides <b>${m.active}</b></div>
        <div class="kpi">GMV <b>NT$${m.gmv.toLocaleString()}</b></div>
        <div class="kpi">Avg ticket <b>NT$${m.avg.toLocaleString()}</b></div>
        <div class="kpi">Drivers online <b>${m.drivers_online}</b></div>
        <div class="kpi">Vehicles <b>${m.vehicles}</b></div>
        <div class="kpi">Conversion <b>${m.conversion}%</b></div>
      </div>
      <p class="sub">Live dispatch runs on the attached Fleet OS — not a rebuilt clone.</p>
      <a class="btn btn-p" href="${FLEET}" target="_blank" rel="noopener">Open Fleet Dispatch</a>
      <a class="btn btn-g" href="/app.html">Customer app</a>`;
  }
  if (view === "book") {
    const rows = await VELORA.get("/api/bookings");
    const drivers = await VELORA.get("/api/drivers");
    panel.innerHTML = `<h1>Booking management</h1>
      <p class="sub">Assign drivers, sync flights, dispatch replacement cars after incidents.</p>` +
      rows.map((b) => `<article class="panel" style="margin:10px 0">
      <b>${b.id}</b> <span class="status">${b.status}</span> · ${b.channel || "web"} · ${b.email}<br/>
      ${b.pickup.name} → ${b.dest.name} · ${b.quote.symbol}${b.quote.breakdown.total}
      ${b.driver ? `<br/>Driver <b>${b.driver.first}</b> ★ ${b.driver.rating}` : ""}
      ${b.live && b.live.flight ? `<br/><span class="pill warn">Flight ${b.live.flight.code} · ${b.live.flight.delay_min || 0} min delay</span>` : ""}
      ${b.replacement ? `<br/><span class="pill red">Replacement ${b.replacement.first} · ${b.replacement.plate || ""}</span>` : ""}
      ${alertHtml(b)}
      <div class="ios-row" style="margin-top:10px">
        <select data-as="${b.id}">${drivers.map((d) => `<option value="${d.id}" ${d.id===b.driver_id?"selected":""}>${d.first} · ${d.status}</option>`).join("")}</select>
        <button class="btn btn-p" data-assign="${b.id}">Assign</button>
        <button class="btn btn-g" data-track="${b.id}">Live</button>
      </div>
      <div class="ios-row" style="margin-top:8px">
        <button class="btn btn-g" data-ops="${b.id}" data-k="flight_sync">Sync flight</button>
        <button class="btn btn-g" data-ops="${b.id}" data-k="change_driver">Swap driver</button>
        <button class="btn btn-g" data-ops="${b.id}" data-k="driver_late">Driver late</button>
        <button class="btn btn-g" data-ops="${b.id}" data-k="passenger_late">Passenger late</button>
        <button class="btn btn-g" data-ops="${b.id}" data-k="incident">Accident / replace</button>
        <button class="btn btn-g" data-can="${b.id}">Cancel</button>
      </div>
    </article>`).join("") || "<p>No bookings.</p>";
    panel.querySelectorAll("[data-assign]").forEach((btn) => btn.onclick = async () => {
      const sel = panel.querySelector(`[data-as="${btn.dataset.assign}"]`);
      await VELORA.post("/api/bookings/" + btn.dataset.assign + "/assign", { driver_id: sel.value });
      paint();
    });
    panel.querySelectorAll("[data-track]").forEach((btn) => btn.onclick = () => {
      location.href = "/track.html?id=" + encodeURIComponent(btn.dataset.track);
    });
    panel.querySelectorAll("[data-ops]").forEach((btn) => btn.onclick = async () => {
      const body = { kind: btn.dataset.k };
      if (btn.dataset.k === "change_driver") {
        const sel = panel.querySelector(`[data-as="${btn.dataset.ops}"]`);
        body.driver_id = sel.value;
      }
      if (btn.dataset.k === "incident") body.note = "Ops: vehicle incident";
      await VELORA.post("/api/bookings/" + btn.dataset.ops + "/ops", body);
      paint();
    });
    panel.querySelectorAll("[data-can]").forEach((btn) => btn.onclick = async () => {
      await VELORA.post("/api/bookings/" + btn.dataset.can + "/cancel", {});
      paint();
    });
  }
  if (view === "manual") {
    panel.innerHTML = `<h1>Phone / hotel / walk-in</h1>
      <form class="panel" id="man">
        <select name="pickup_id">${catalog.locations.map((l)=>`<option value="${l.id}">${l.name}</option>`).join("")}</select>
        <select name="dest_id">${catalog.locations.map((l)=>`<option value="${l.id}" ${l.id==="taipei-101"?"selected":""}>${l.name}</option>`).join("")}</select>
        <input name="when" type="datetime-local" required/>
        <input name="first" value="Hotel Guest" required/>
        <input name="last" value="Desk"/>
        <input name="email" value="desk@velora.demo"/>
        <input name="phone" value="+8862"/>
        <input name="flight" placeholder="CI 011"/>
        <select name="payment"><option value="invoice">Invoice</option><option value="cash">Cash</option><option value="card">Card</option></select>
        <button class="btn btn-p">Create booking</button>
      </form>`;
    document.getElementById("man").onsubmit = async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      await VELORA.post("/api/bookings", {
        pickup_id: fd.get("pickup_id"), dest_id: fd.get("dest_id"), when: fd.get("when"),
        first: fd.get("first"), last: fd.get("last"), email: fd.get("email"), phone: fd.get("phone"),
        flight: fd.get("flight") || "", track_flight: Boolean(fd.get("flight")),
        payment: fd.get("payment"), class_id: "standard", pax: 2, bags: 2, terms: true, guest: true, channel: "phone",
      });
      view = "book"; paint();
    };
  }
  if (view === "channels") {
    const ch = await VELORA.get("/api/admin/channels");
    const jobs = await VELORA.get("/api/fleet/jobs");
    panel.innerHTML = `<h1>Channels → Fleet OS</h1>
      <p class="sub">Every VELORA, Klook and partner order syncs into the Fleet OS dispatch queue automatically.</p>
      <div class="kpis">
        ${ch.channels.map((c) => `<div class="kpi">${c.name}<b>${ch.bookings_by_channel[c.id] || 0}</b><span class="sub">${c.desc}</span></div>`).join("")}
        <div class="kpi">Fleet jobs queued<b>${ch.fleet_jobs_queued}</b></div>
        <div class="kpi">Fleet jobs dispatched<b>${ch.fleet_jobs_dispatched}</b></div>
      </div>
      <p><a class="btn btn-p" href="${FLEET}" target="_blank" rel="noopener">Open Fleet OS dispatch</a></p>
      <h2>Recent sync queue</h2>` +
      (jobs.slice(0, 10).map((j) => `<article class="panel" style="margin:8px 0">
        <b>${j.id}</b> · <span class="status">${j.status}</span> · channel <b>${j.channel}</b>
        ${j.external_id ? `· ext ${j.external_id}` : ""}<br/>
        ${j.booking_id} · ${j.pickup.name} → ${j.dest.name} · NT$${j.total_twd.toLocaleString()}
        ${j.status === "queued" ? `<button class="btn btn-g" data-ack="${j.id}" style="margin-top:8px">Mark dispatched</button>` : ""}
      </article>`).join("") || "<p>No fleet jobs yet.</p>");
    panel.querySelectorAll("[data-ack]").forEach((b) => b.onclick = async () => {
      await VELORA.post("/api/fleet/jobs/" + b.dataset.ack + "/ack", {});
      paint();
    });
  }
  if (view === "fleet") {
    panel.innerHTML = `<h1>Fleet OS</h1>
      <p class="sub">Attached live prototype — VELORA does not reimplement this console.</p>
      <p><a class="btn btn-p" href="${FLEET}" target="_blank" rel="noopener">${FLEET}</a></p>
      <iframe class="fleet" title="Fleet Dispatch" src="${FLEET}"></iframe>`;
  }
  if (view === "drivers") {
    const ds = await VELORA.get("/api/drivers");
    panel.innerHTML = `<h1>Drivers & vehicles</h1>` + ds.map((d) => `<div class="panel" style="margin:8px 0">
      <img src="${d.photo}" alt="" width="40" height="40" style="border-radius:50%;vertical-align:middle;margin-right:8px"/>
      <b>${d.first} ${d.last}</b> · ${d.status} · ★ ${d.rating}
      <a class="chip" href="/api/drivers/${d.id}/profile" target="_blank">Profile</a>
      <button class="chip" data-t="${d.id}">Toggle</button></div>`).join("");
    panel.querySelectorAll("[data-t]").forEach((b) => b.onclick = async () => { await VELORA.post("/api/drivers/" + b.dataset.t + "/toggle", {}); paint(); });
  }
  if (view === "pricing") {
    panel.innerHTML = `<h1>Pricing engine</h1>
      <p>Base NT$420 · per km 28 · per min 6 · airport 80 · night 18% · stop 180 · service 4%.</p>
      <p>Fixed routes override distance (example TPE → Taipei 101 NT$1,380 before class multiplier).</p>
      <p>Promos: VELORA10, AIRPORT200, NEWGUEST. Surge architecture ready, disabled.</p>`;
  }
}

async function boot() {
  catalog = await VELORA.get("/api/catalog");
  document.querySelectorAll(".aside [data-v]").forEach((b) => b.onclick = () => {
    document.querySelectorAll(".aside [data-v]").forEach((x) => x.classList.remove("on"));
    b.classList.add("on"); view = b.dataset.v; paint();
  });
  paint();
}
boot();
