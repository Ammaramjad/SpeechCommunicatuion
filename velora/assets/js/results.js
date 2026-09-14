document.getElementById("chrome-header").innerHTML = headerHTML();
document.getElementById("chrome-footer").innerHTML = footerHTML();
bindChrome();

const q = Object.fromEntries(new URLSearchParams(location.search));
const body = {
  service: q.service || "airport",
  mode: q.mode || "pickup",
  pickup_id: q.pickup_id || "tpe",
  dest_id: q.dest_id || "taipei-101",
  when: q.when || tomorrow(),
  pax: Number(q.pax || 2),
  bags: Number(q.bags || 2),
  hours: Number(q.hours || 8),
  roundtrip: q.roundtrip === "true",
  return_when: q.return_when || "",
  flight: q.flight || "",
  meet: q.meet !== "false",
  currency: VELORA.currency,
};

let rows = [];
let summaryMeta = "";

async function run() {
  document.getElementById("summary").textContent = `Searching vehicles… ${body.pickup_id} → ${body.dest_id}`;
  try {
    const res = await VELORA.post("/api/search", body);
    VELORA.track("search_completed", { count: res.count });
    rows = res.results;
    summaryMeta = `${res.pickup.name} → ${res.dest.name} · ${body.pax} pax · ${body.bags} bags`;
    document.getElementById("summary").textContent = `${res.count} vehicles · ${summaryMeta}`;
    draw();
  } catch (e) {
    document.getElementById("summary").textContent = "Location not recognized or search failed. Try a listed airport or landmark.";
  }
}

function draw() {
  const pmax = Number(document.getElementById("pmax").value);
  const instant = document.getElementById("instant").checked;
  const ev = document.getElementById("ev").checked;
  const prem = document.getElementById("prem").checked;
  const wheel = document.getElementById("wheel").checked;
  let list = rows.filter((r) => r.price.breakdown.total <= pmax);
  if (instant) list = list.filter((r) => r.instant);
  if (ev) list = list.filter((r) => r.class.ev);
  if (prem) list = list.filter((r) => r.class.premium);
  if (wheel) list = list.filter((r) => r.class.wheelchair);
  if (document.getElementById("meet").checked) list = list.filter((r) => r.class.meet);
  const sort = document.getElementById("sort").value;
  list.sort((a, b) => {
    if (sort === "price") return a.price.breakdown.total - b.price.breakdown.total;
    if (sort === "phigh") return b.price.breakdown.total - a.price.breakdown.total;
    if (sort === "rate") return b.operator.rating - a.operator.rating;
    if (sort === "pop") return (b.popular?1:0) - (a.popular?1:0);
    return (b.popular?1:0) - (a.popular?1:0) || a.price.breakdown.total - b.price.breakdown.total;
  });
  document.getElementById("empty").hidden = list.length > 0;
  document.getElementById("summary").textContent = `${list.length} vehicles · ${summaryMeta}`;
  document.getElementById("list").innerHTML = list.map((r, i) => `
    <article class="result" style="animation-delay:${i*40}ms">
      <img src="${r.class.img}" alt="${r.class.name}"/>
      <div>
        <span class="badge">${r.instant ? "Instant confirmation" : "On request"}</span>
        ${r.free_cancel ? `<span class="badge">Free cancel &gt;24h</span>` : ""}
        <h3>${r.class.name}</h3>
        <p class="sub">${r.class.example} · ${r.operator.name} ★ ${r.operator.rating} (${r.operator.rides.toLocaleString()} rides)</p>
        <div class="icons">
          <span>👥 ${r.class.pax}</span><span>🧳 ${r.class.bags}</span><span>❄️ AC</span>
          <span>🚪 ${r.class.doors}</span>${r.class.auto?"<span>AT</span>":""}${r.class.ev?"<span>EV</span>":""}
        </div>
        <p class="sub">${r.distance} km · ${r.duration} min · waiting policy on voucher</p>
      </div>
      <div>
        <div class="price">${r.price.symbol}${r.price.breakdown.total.toLocaleString()}</div>
        <p class="sub">per vehicle · taxes in total</p>
        <a class="btn btn-p" href="/ride.html?${new URLSearchParams({...body, class_id: r.class.id}).toString()}">${VELORA.t("select")}</a>
      </div>
    </article>`).join("");
}

["pmax","instant","ev","prem","wheel","sort","cancel","meet"].forEach((id) => {
  const el = document.getElementById(id);
  if (el) el.addEventListener("change", draw);
});
document.getElementById("modify").onclick = () => location.href = "/#search";
const openF = document.getElementById("openFilters");
if (openF) openF.onclick = () => document.querySelector(".filters").classList.toggle("open");
run();
