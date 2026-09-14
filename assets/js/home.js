document.getElementById("chrome-header").innerHTML = headerHTML("book");
document.getElementById("chrome-footer").innerHTML = footerHTML();
document.getElementById("heroTitle").textContent = VELORA.t("hero");
document.getElementById("heroLede").textContent = VELORA.t("lede");
bindChrome();
VELORA.track("homepage_viewed");

const state = { service: "airport", catalog: null, region: "tw" };

function idFromInput(val) {
  const hit = state.catalog.locations.find((l) => l.name === val || l.id === val);
  return hit ? hit.id : "tpe";
}

function money(n) {
  return VELORA.money(n, VELORA.currency);
}

function renderSubnav() {
  const el = document.getElementById("subnav");
  if (!el || !state.catalog.secondary_nav) return;
  el.innerHTML = state.catalog.secondary_nav.map((l) => `<a href="${VELORA.url(l.href)}">${l.label}</a>`).join("");
}

function renderServiceTabs() {
  const el = document.getElementById("serviceTabs");
  if (!el) return;
  el.innerHTML = state.catalog.service_tabs.map((t) => `
    <button type="button" class="svc-tab ${t.id === state.service ? "on" : ""}" data-svc="${t.id}">
      <span>${t.icon}</span>
      <div>${t.label}<small>${t.desc}</small></div>
    </button>`).join("");
  el.querySelectorAll("[data-svc]").forEach((btn) => btn.onclick = () => {
    const svc = btn.dataset.svc;
    if (svc === "corporate" || svc === "events") {
      location.href = VELORA.url("/help.html#" + svc);
      return;
    }
    state.service = svc;
    document.querySelectorAll(".svc-tab").forEach((x) => x.classList.toggle("on", x.dataset.svc === svc));
    document.querySelectorAll("#coreTabs .tab").forEach((x) => {
      const on = x.dataset.service === svc || (svc === "intercity" && x.dataset.service === "p2p");
      x.setAttribute("aria-selected", on ? "true" : "false");
    });
    if (svc === "hourly") document.getElementById("hoursWrap")?.classList.remove("hidden");
    else document.getElementById("hoursWrap")?.classList.add("hidden");
    document.getElementById("airMode").style.display = svc === "airport" ? "flex" : "none";
    if (svc === "intercity") state.service = "p2p";
  });
}

function renderRegions() {
  const el = document.getElementById("regionPills");
  if (!el) return;
  el.innerHTML = state.catalog.regions.map((r) => `
    <button type="button" class="region-pill ${r.id === state.region ? "on" : ""}" data-r="${r.id}">${r.label}</button>`).join("");
  el.querySelectorAll("[data-r]").forEach((b) => b.onclick = () => {
    state.region = b.dataset.r;
    el.querySelectorAll(".region-pill").forEach((x) => x.classList.toggle("on", x.dataset.r === state.region));
    if (state.region !== "tw") VELORA.track("region_browse", { region: state.region });
  });
}

function renderDestinations() {
  const el = document.getElementById("destCarousel");
  if (!el) return;
  el.innerHTML = state.catalog.destinations.map((d) => `
    <article class="dest-card" data-loc="${d.loc}" tabindex="0">
      <img src="${d.img}" alt="${d.name}" loading="lazy"/>
      <div class="meta"><b>${d.name}</b><span>${d.rides.toLocaleString()} rides</span></div>
    </article>`).join("");
  el.querySelectorAll(".dest-card").forEach((c) => c.onclick = () => {
    const loc = state.catalog.locations.find((l) => l.id === c.dataset.loc);
    if (loc) {
      document.getElementById("pickup").value = loc.kind === "airport" ? loc.name : "Taoyuan International Airport (TPE)";
      document.getElementById("dest").value = loc.kind === "airport" ? "Taipei 101 / Xinyi" : loc.name;
      document.getElementById("search").scrollIntoView({ behavior: "smooth" });
    }
  });
}

function renderFavorites() {
  const el = document.getElementById("favorites");
  if (!el) return;
  el.innerHTML = state.catalog.favorites.map((f) => `
    <article class="fav-card">
      <img src="${f.img}" alt="${f.title}" loading="lazy"/>
      <div class="fav-body">
        <div class="fav-cat">${f.cat}</div>
        <h3 class="fav-title">${f.title}</h3>
        <div class="fav-meta">★ ${f.stars} · ${f.reviews.toLocaleString()} reviews · ${f.booked} booked</div>
        <div class="fav-tags">
          <span class="tag">${f.badge}</span>
          ${f.instant ? '<span class="tag grey">Instant confirmation</span>' : ""}
          ${f.cancel ? '<span class="tag grey">Free cancellation</span>' : ""}
        </div>
        <div class="fav-foot">
          <span class="fav-price">${money(f.price)}</span>
          <button class="btn btn-p" type="button" data-fav="${f.id}">Book</button>
        </div>
      </div>
    </article>`).join("");
  el.querySelectorAll("[data-fav]").forEach((btn) => {
    const f = state.catalog.favorites.find((x) => x.id === btn.dataset.fav);
    btn.onclick = () => go({
      service: f.service || "airport",
      pickup_id: f.from,
      dest_id: f.to,
      class_id: f.class_id,
    });
  });
}

function renderPromos() {
  const el = document.getElementById("promos");
  if (!el) return;
  el.innerHTML = state.catalog.promo_shelf.map((p) => `
    <div class="promo-card">
      <b>${p.label}</b>
      <p class="sub">${p.type === "pct" ? p.value + "% off" : "NT$" + p.value + " off"}${p.min ? " · min spend NT$" + p.min : ""}</p>
      <p><code>${p.code}</code></p>
    </div>`).join("");
}

function renderBenefits() {
  const el = document.getElementById("benefits");
  if (!el) return;
  el.innerHTML = state.catalog.benefits.map((b) => `
    <div class="benefit"><div class="ico">${b.icon}</div><h3>${b.title}</h3><p>${b.text}</p></div>`).join("");
}

function renderHowBook() {
  const el = document.getElementById("howBook");
  if (!el) return;
  el.innerHTML = state.catalog.how_to_book.map((s) => `
    <div><div class="num">${s.step}</div><h3>${s.title}</h3><p class="sub">${s.text}</p></div>`).join("");
}

function renderTrending() {
  const el = document.getElementById("trending");
  if (!el) return;
  el.innerHTML = state.catalog.trending.map((t, i) => `<button type="button" data-t="${i}">${i + 1}. ${t}</button>`).join("");
  const routes = [
    { from: "tpe", to: "taipei-101" }, { from: "tpe", to: "jiufen" }, { from: "tsa", to: "taipei-101" },
    { from: "tpe", to: "hsr-ty" }, { from: "khh", to: "formosa-blvd" }, { from: "rmq", to: "taichung-st" },
    { from: "taipei-main", to: "taipei-101", service: "hourly" }, { from: "tpe", to: "taipei-101" },
  ];
  el.querySelectorAll("[data-t]").forEach((b) => {
    const r = routes[Number(b.dataset.t)] || routes[0];
    b.onclick = () => go({ pickup_id: r.from, dest_id: r.to, service: r.service || "airport" });
  });
}

async function boot() {
  state.catalog = await VELORA.get("/api/catalog");
  try {
    const m = await VELORA.get("/api/admin/metrics");
    const el = document.getElementById("kpis");
    if (el) {
      const tiles = el.querySelectorAll("b");
      tiles[0].textContent = m.drivers_online;
      tiles[1].textContent = m.active;
      tiles[2].textContent = "NT$" + m.gmv.toLocaleString();
      tiles[3].textContent = "NT$" + m.avg.toLocaleString();
    }
  } catch (_) {}
  renderSubnav();
  renderServiceTabs();
  renderRegions();
  renderDestinations();
  renderFavorites();
  renderPromos();
  renderBenefits();
  renderHowBook();
  renderTrending();
  document.getElementById("locs").innerHTML = state.catalog.locations.map((l) => `<option value="${l.name}"></option>`).join("");
  document.getElementById("pickup").value = "Taoyuan International Airport (TPE)";
  document.getElementById("dest").value = "Taipei 101 / Xinyi";
  document.getElementById("when").value = tomorrow();
  document.getElementById("popular").innerHTML = state.catalog.popular.map((r, i) => {
    const a = state.catalog.locations.find((x) => x.id === r.from);
    const b = state.catalog.locations.find((x) => x.id === r.to);
    return `<article class="card" style="animation-delay:${i * 60}ms"><div class="pad">
      <span class="badge">${r.mins} min</span>
      <h3>${a.city} · ${a.id.toUpperCase()} → ${b.name.split(",")[0]}</h3>
      <p class="sub">${a.name}<br/>${b.name}</p>
      <button class="btn btn-p" data-from="${r.from}" data-to="${r.to}">Search this route</button>
    </div></article>`;
  }).join("");
  document.getElementById("classes").innerHTML = state.catalog.classes.map((c) => `<article class="card">
    <img src="${c.img}" alt="${c.name}"/>
    <div class="pad"><h3>${c.name}</h3><p class="sub">${c.example}<br/>${c.pax} pax · ${c.bags} bags</p></div></article>`).join("");
  document.getElementById("reviews").innerHTML = state.catalog.reviews.map((r) => `<article class="card"><div class="pad">
    <b>★ ${r.stars} · ${r.name}</b><p class="sub">${r.ride}<br/>${r.text}</p><p class="sub">${r.date}</p></div></article>`).join("");
  document.getElementById("faq").innerHTML = state.catalog.faq.map((f) => `<details><summary>${f.q}</summary><p class="sub">${f.a}</p></details>`).join("");
  document.querySelectorAll("[data-from]").forEach((b) => b.onclick = () => go({ pickup_id: b.dataset.from, dest_id: b.dataset.to }));
  const rec = VELORA.recent();
  if (rec.length) {
    document.getElementById("recent").innerHTML = "Recent: " + rec.map((s, i) => `<button type="button" class="chip" data-r="${i}">${s.pickup_id} → ${s.dest_id}</button>`).join(" ");
    document.querySelectorAll("[data-r]").forEach((b) => b.onclick = () => go(rec[Number(b.dataset.r)]));
  }
  const appClose = document.getElementById("appClose");
  if (appClose) appClose.onclick = () => document.getElementById("appWidget")?.classList.add("hidden");
}

function go(params) {
  const trip = (document.querySelector('[name=trip]:checked') || {}).value === "round";
  const q = new URLSearchParams({
    service: params.service || state.service,
    pickup_id: params.pickup_id,
    dest_id: params.dest_id,
    when: params.when || document.getElementById("when").value,
    pax: params.pax || document.getElementById("pax").value,
    bags: params.bags || document.getElementById("bags").value,
    hours: params.hours || document.querySelector('[name=hours]')?.value || "8",
    roundtrip: String(params.roundtrip ?? trip),
    return_when: document.getElementById("returnWhen").value || "",
    mode: (document.querySelector('[name=mode]:checked') || {}).value || "pickup",
    flight: (document.querySelector('[name=flight]') || {}).value || "",
    meet: String(document.querySelector('[name=meet]')?.checked !== false),
    track: String(document.querySelector('[name=track]')?.checked !== false),
    currency: VELORA.currency,
    class_id: params.class_id || "",
  });
  VELORA.saveSearch(Object.fromEntries(q));
  VELORA.track("search_started", Object.fromEntries(q));
  location.href = VELORA.url("/results.html?" + q.toString());
}

document.querySelectorAll("#coreTabs .tab").forEach((t) => t.onclick = () => {
  document.querySelectorAll("#coreTabs .tab").forEach((x) => x.setAttribute("aria-selected", "false"));
  t.setAttribute("aria-selected", "true");
  state.service = t.dataset.service;
  document.querySelectorAll(".svc-tab").forEach((x) => x.classList.toggle("on", x.dataset.svc === state.service));
  document.getElementById("hoursWrap").classList.toggle("hidden", state.service !== "hourly");
  document.getElementById("airMode").style.display = state.service === "airport" ? "flex" : "none";
});
document.getElementById("swap").onclick = () => {
  const a = document.getElementById("pickup"); const b = document.getElementById("dest");
  const t = a.value; a.value = b.value; b.value = t;
};
document.querySelectorAll('[name=trip]').forEach((r) => r.onchange = () => {
  const round = document.querySelector('[name=trip][value=round]').checked;
  document.getElementById("returnWrap").classList.toggle("hidden", !round);
});
document.getElementById("search").onsubmit = (e) => {
  e.preventDefault();
  go({
    pickup_id: idFromInput(document.getElementById("pickup").value),
    dest_id: idFromInput(document.getElementById("dest").value),
    hours: document.querySelector('[name=hours]')?.value,
  });
};

boot();
