document.getElementById("chrome-header").innerHTML = headerHTML("book");
document.getElementById("chrome-footer").innerHTML = footerHTML();
document.getElementById("heroTitle").textContent = VELORA.t("hero");
document.getElementById("heroLede").textContent = VELORA.t("lede");
bindChrome();
VELORA.track("homepage_viewed");

const state = { service: "airport", catalog: null };

function idFromInput(val) {
  const hit = state.catalog.locations.find((l) => l.name === val || l.id === val);
  return hit ? hit.id : "tpe";
}

async function boot() {
  state.catalog = await VELORA.get("/api/catalog");
  document.getElementById("locs").innerHTML = state.catalog.locations.map((l) => `<option value="${l.name}"></option>`).join("");
  document.getElementById("pickup").value = "Taoyuan International Airport (TPE)";
  document.getElementById("dest").value = "Taipei 101 / Xinyi";
  document.getElementById("when").value = tomorrow();
  document.getElementById("popular").innerHTML = state.catalog.popular.map((r, i) => {
    const a = state.catalog.locations.find((x) => x.id === r.from);
    const b = state.catalog.locations.find((x) => x.id === r.to);
    return `<article class="card" style="animation-delay:${i*60}ms"><div class="pad">
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
}

function go(params) {
  const q = new URLSearchParams({
    service: params.service || state.service,
    pickup_id: params.pickup_id,
    dest_id: params.dest_id,
    when: params.when || document.getElementById("when").value,
    pax: params.pax || document.getElementById("pax").value,
    bags: params.bags || document.getElementById("bags").value,
    roundtrip: params.roundtrip || (document.querySelector('[name=trip]:checked') || {}).value === "round",
    mode: (document.querySelector('[name=mode]:checked') || {}).value || "pickup",
    currency: VELORA.currency,
  });
  VELORA.saveSearch(Object.fromEntries(q));
  VELORA.track("search_started", Object.fromEntries(q));
  location.href = "/results.html?" + q.toString();
}

document.querySelectorAll(".tab").forEach((t) => t.onclick = () => {
  document.querySelectorAll(".tab").forEach((x) => x.setAttribute("aria-selected", "false"));
  t.setAttribute("aria-selected", "true");
  state.service = t.dataset.service;
  document.getElementById("hoursWrap").classList.toggle("hidden", state.service !== "hourly");
  document.getElementById("airMode").style.display = state.service === "airport" ? "flex" : "none";
});
document.getElementById("swap").onclick = () => {
  const a = document.getElementById("pickup"); const b = document.getElementById("dest");
  const t = a.value; a.value = b.value; b.value = t;
};
document.querySelectorAll('[name=trip]').forEach((r) => r.onchange = () => {
  document.getElementById("returnWrap").classList.toggle("hidden", r.value !== "round" && !document.querySelector('[name=trip][value=round]').checked);
});
document.getElementById("searchForm").onsubmit = (e) => {
  e.preventDefault();
  go({
    pickup_id: idFromInput(document.getElementById("pickup").value),
    dest_id: idFromInput(document.getElementById("dest").value),
    hours: document.querySelector('[name=hours]').value,
  });
};

boot();
