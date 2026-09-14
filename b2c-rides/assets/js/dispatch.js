let catalog, map, markers = [], view = "dash";

function stClass(s) { return "st st-" + s; }

function jobsHtml(jobs, drivers) {
  return jobs.map((b) => `
    <div class="job">
      <div>
        <span class="${stClass(b.status)}">${b.status}</span>
        <b> ${b.id}</b> · ${b.channel} · ${b.type}<br/>
        ${RL.loc(b.from_place)} → ${RL.loc(b.to_place)}<br/>
        ${RL.car(b.vehicle)} · ${RL.nt(b.fare.total)} · OTP ${b.otp}
        ${b.driver ? `<div>司機 ${b.driver.name} ${b.driver.plate}</div>` : `<div class="rank">未指派</div>`}
        ${b.itri ? `<div class="rank">ITRI score ${b.itri.score} · ${b.itri.km} km</div>` : ""}
      </div>
      <div>
        ${b.status === "new" ? `<select data-assign="${b.id}">${drivers.filter(d=>d.status==='available').map(d=>`<option value="${d.id}">${d.name}</option>`).join("")}</select>
        <button class="btn btn-k" data-do="assign" data-id="${b.id}">${RL.t("assign")}</button>` : ""}
        ${b.status === "assigned" ? `<button class="pill" data-do="status" data-id="${b.id}" data-s="accepted">${RL.t("accept")}</button>` : ""}
        ${["accepted","arriving","onboard"].includes(b.status) ? `<button class="btn btn-k" data-do="status" data-id="${b.id}" data-s="completed">${RL.t("complete")}</button>` : ""}
        ${!["completed","cancelled"].includes(b.status) ? `<button class="pill" data-do="status" data-id="${b.id}" data-s="cancelled">${RL.t("cancelled")}</button>` : ""}
      </div>
    </div>`).join("") || "<p>No jobs</p>";
}

async function paint() {
  const sum = await API.get("/api/fleet/summary");
  const jobs = await API.get("/api/bookings");
  const drivers = await API.get("/api/drivers");
  const itri = await API.get("/api/fleet/itri");
  const an = await API.get("/api/fleet/analytics");
  const live = await API.get("/api/live/marketplace");

  document.getElementById("kpis").innerHTML = `
    <div class="kpi"><span>即時工單</span><b>${sum.active_jobs}</b></div>
    <div class="kpi"><span>可接單</span><b>${sum.available_drivers}</b></div>
    <div class="kpi"><span>GMV</span><b>${RL.nt(sum.gmv)}</b></div>
    <div class="kpi"><span>Web / App / Phone</span><b>${sum.channels.web}/${sum.channels.app}/${sum.channels.dispatch}</b></div>`;

  const panel = document.getElementById("panel");

  if (view === "dash") {
    panel.innerHTML = `
      <div style="display:flex;gap:8px;margin:8px 0">
        <button class="btn btn-k" id="auto">${RL.t("assign")} · ITRI auto</button>
      </div>
      <h3>動態路線卡片</h3>
      <div class="grid4">${live.cards.slice(0,4).map((c)=>`<div class="kpi"><b>${RL.loc(c.from_place)} → ${RL.loc(c.to_place)}</b>
        <div>${RL.nt(c.live_price)} · ${c.available} 輛 · ${c.booked_today} 訂</div>
        <div class="bar"><i style="width:${Math.min(100,c.booked_today*22)}%"></i></div></div>`).join("")}</div>
      <div id="fmap"></div>
      <div style="display:grid;grid-template-columns:1.3fr .7fr;gap:14px">
        <div><h3>訂單佇列</h3><div id="jobs">${jobsHtml(jobs, drivers)}</div></div>
        <div>
          <form id="phoneForm"></form>
          <h3>Alerts</h3><div id="alerts">${(sum.alerts||[]).map(a=>`<div class="sub">${a.message}</div>`).join("")}</div>
        </div>
      </div>`;
    mountMap();
    fillPhone();
    document.getElementById("auto").onclick = async () => { await API.post("/api/fleet/auto-dispatch", {}); paint(); };
  }

  if (view === "jobs") {
    panel.innerHTML = `<h3>全部訂單（web / app / 電話）</h3><div id="jobs">${jobsHtml(jobs, drivers)}</div>`;
  }

  if (view === "map") {
    panel.innerHTML = `<div id="fmap" style="height:520px"></div>`;
    mountMap();
  }

  if (view === "roster") {
    panel.innerHTML = `<h3>車隊名冊</h3>${drivers.map((d)=>`
      <div class="job"><div><b>${d.name}</b> · ${d.plate} · ${d.vehicle}<br/>${d.status} · ★ ${d.rating} · ${d.lang.join(", ")} · ${d.shift || ""}</div>
      <button class="pill" data-toggle="${d.id}">${d.status==="offline"?RL.t("online"):RL.t("offline")}</button></div>`).join("")}`;
  }

  if (view === "schedule") {
    panel.innerHTML = `<h3>白班 / 夜班</h3>${itri.shifts.map((s)=>`<div class="kpi"><b>${RL.lang==="en"?s.name_en:s.name_zh}</b>
      <p>${s.drivers.map((id)=>{ const d=drivers.find(x=>x.id===id); return d?d.name:id; }).join(" · ")}</p></div>`).join("")}`;
  }

  if (view === "itri") {
    panel.innerHTML = `
      <h3>工研院 ITRI 派車引擎</h3>
      <p class="sub">分車 · 區域路線 · 站點順序 · Rank Aggregation · 圖資 ${itri.map_engines.join(" / ")}（目前 ${itri.engine}）</p>
      <p>準點 ${itri.on_time}% · 空車 ${itri.empty_km} km · 排程 ${itri.schedule_minutes} 分</p>
      <button class="btn btn-k" id="auto">一鍵自動派車</button>
      ${itri.queue.map((q)=>`<div class="job"><div>
        <b>${q.booking.id}</b> ${RL.loc(q.booking.from_place)} → ${RL.loc(q.booking.to_place)}
        ${q.ranking.map((r,i)=>`<div class="rank">#${i+1} ${r.driver_id} score ${r.score} · ${r.km}km</div>`).join("")}
      </div></div>`).join("") || "<p>佇列已清空</p>"}
      <h3>運力分區</h3>
      ${itri.zones.map((z)=>`<div class="kpi"><b>${RL.lang==="en"?z.name_en:z.name_zh}</b>
        load ${z.load}% · empty ${z.empty_km}km <div class="bar"><i style="width:${z.load}%"></i></div></div>`).join("")}`;
    const auto = document.getElementById("auto");
    if (auto) auto.onclick = async () => { await API.post("/api/fleet/auto-dispatch", {}); paint(); };
  }

  if (view === "forecast") {
    panel.innerHTML = `<h3>產能預測</h3>${an.forecast.map((f)=>`<div class="kpi"><b>${f.hour}</b> demand ${f.demand}
      <div class="bar"><i style="width:${f.demand*3}%"></i></div></div>`).join("")}`;
  }

  if (view === "analytics") {
    panel.innerHTML = `<h3>數據分析報表</h3>
      <div class="kpis">
        <div class="kpi">完成率 <b>${an.completion_rate}%</b></div>
        <div class="kpi">取消率 <b>${an.cancel_rate}%</b></div>
        <div class="kpi">GMV <b>${RL.nt(an.gmv)}</b></div>
        <div class="kpi">總單 <b>${an.total}</b></div>
      </div>
      <pre class="sub">${JSON.stringify(an.by_type, null, 2)}</pre>`;
  }

  if (view === "sos") {
    panel.innerHTML = `<h3>安全中心</h3>
      <button class="btn btn-k" data-al="交通事故">交通事故</button>
      <button class="btn btn-ghost" data-al="車輛故障">車輛故障</button>
      <button class="btn btn-ghost" data-al="醫療緊急">醫療緊急</button>
      <div id="alerts">${(sum.alerts||[]).map(a=>`<div class="sub">${a.level}: ${a.message}</div>`).join("")}</div>`;
    panel.querySelectorAll("[data-al]").forEach((b) => b.onclick = async () => {
      await API.post("/api/fleet/alert", { message: b.dataset.al, level: "critical" });
      paint();
    });
  }

  bindActions();
}

function mountMap() {
  const el = document.getElementById("fmap");
  if (!el || typeof L === "undefined") return;
  if (map) { try { map.remove(); } catch (e) {} map = null; markers = []; }
  map = L.map(el).setView([25.04, 121.52], 8);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OSM" }).addTo(map);
  API.get("/api/drivers").then((drivers) => {
    drivers.forEach((d) => {
      L.circleMarker([d.lat, d.lng], { radius: 8, color: d.status === "available" ? "#6ee7a8" : d.status === "busy" ? "#ff5b00" : "#64748b", fillOpacity: 1 })
        .addTo(map).bindPopup(`${d.name}<br/>${d.plate}<br/>${d.status}`);
    });
  });
  setTimeout(() => map && map.invalidateSize(), 200);
}

function fillPhone() {
  const form = document.getElementById("phoneForm");
  if (!form || !catalog) return;
  const sel = (name, rows, lab) => `<select name="${name}">${rows.map((p)=>`<option value="${p.id}">${lab(p)}</option>`).join("")}</select>`;
  form.innerHTML = `<h3>${RL.t("phoneBook")}</h3>
    <select name="type"><option value="airport_pickup">接機</option><option value="airport_drop">送機</option><option value="instant">立即叫車</option><option value="hourly">包車</option><option value="p2p">城際</option></select>
    ${sel("from_id", catalog.places, RL.loc)}
    ${sel("to_id", catalog.places, RL.loc)}
    <input name="when" type="datetime-local" required />
    <input name="pax" type="number" value="2"/>
    ${sel("vehicle_id", catalog.vehicles, RL.car)}
    <input name="name" value="陳先生"/>
    <input name="phone" value="0988-123-456"/>
    <input name="flight" value="CI 160"/>
    <button class="btn btn-k" type="submit">${RL.t("phoneBook")}</button>`;
  form.onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    await API.post("/api/bookings", {
      channel: "dispatch", type: fd.get("type"), from_id: fd.get("from_id"), to_id: fd.get("to_id"),
      when: fd.get("when"), pax: Number(fd.get("pax")), vehicle_id: fd.get("vehicle_id"),
      name: fd.get("name"), phone: fd.get("phone"), flight: fd.get("flight"), meet: true,
    });
    paint();
  };
}

function bindActions() {
  document.querySelectorAll("[data-do='assign']").forEach((btn) => btn.onclick = async () => {
    const sel = document.querySelector(`[data-assign="${btn.dataset.id}"]`);
    if (!sel || !sel.value) return;
    await API.post(`/api/bookings/${btn.dataset.id}/assign`, { driver_id: sel.value });
    paint();
  });
  document.querySelectorAll("[data-do='status']").forEach((btn) => btn.onclick = async () => {
    await API.post(`/api/bookings/${btn.dataset.id}/status`, { status: btn.dataset.s });
    paint();
  });
  document.querySelectorAll("[data-toggle]").forEach((btn) => btn.onclick = async () => {
    await API.post(`/api/drivers/${btn.dataset.toggle}/toggle`, {});
    paint();
  });
}

async function boot() {
  catalog = await API.get("/api/catalog");
  document.getElementById("langBtn").onclick = () => RL.toggle();
  document.getElementById("reset").onclick = async () => { await API.post("/api/demo/reset", {}); paint(); };
  document.querySelectorAll(".side [data-view]").forEach((b) => b.onclick = () => {
    document.querySelectorAll(".side [data-view]").forEach((x) => x.classList.remove("on"));
    b.classList.add("on");
    view = b.dataset.view;
    paint();
  });
  await paint();
  setInterval(() => { if (view === "dash" || view === "jobs") paint(); }, 8000);
}
boot();
