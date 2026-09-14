document.getElementById("chrome-header").innerHTML = headerHTML();
document.getElementById("chrome-footer").innerHTML = footerHTML();
bindChrome();

let tab = "home";
let catalog;

async function render() {
  const el = document.getElementById("body");
  if (tab === "home") {
    el.innerHTML = `
      <div class="blob" style="position:absolute;top:40px;right:-40px"></div>
      <p class="sub" style="animation:rise .6s ease">Good evening</p>
      <h1 style="font-family:Fraunces,serif;font-size:34px;margin:0 0 16px;animation:rise .8s ease">A quiet car is waiting.</h1>
      <div class="glass" style="animation:rise 1s ease">
        <p class="sub">Airport · City · Hourly</p>
        <button class="btn btn-p btn-block" data-go="search">Where to?</button>
      </div>
      <div class="glass" style="margin-top:12px">
        <b>Saved</b>
        <p class="sub">TPE · Taipei 101 · W Taipei</p>
      </div>`;
    el.querySelector("[data-go]").onclick = () => { tab = "search"; paintTabs(); render(); };
  }
  if (tab === "search") {
    el.innerHTML = `<h2>Search</h2>
      <div class="field">Pickup<select id="p">${catalog.locations.map(l=>`<option value="${l.id}">${l.name}</option>`).join("")}</select></div>
      <div class="field">Destination<select id="d">${catalog.locations.map(l=>`<option value="${l.id}" ${l.id==="taipei-101"?"selected":""}>${l.name}</option>`).join("")}</select></div>
      <button class="btn btn-p btn-block" id="go">See cars</button>
      <div id="cars"></div>`;
    document.getElementById("go").onclick = async () => {
      const res = await VELORA.post("/api/search", { pickup_id: p.value, dest_id: d.value, when: tomorrow(), pax: 2, bags: 2, currency: VELORA.currency });
      document.getElementById("cars").innerHTML = res.results.slice(0, 5).map((r) => `<div class="glass" style="margin:10px 0;animation:rise .4s ease">
        <b>${r.class.name}</b>
        <div class="price">${r.price.symbol}${r.price.breakdown.total.toLocaleString()}</div>
        <button class="btn btn-p" data-c="${r.class.id}">Book</button>
      </div>`).join("");
      document.querySelectorAll("[data-c]").forEach((b) => b.onclick = () => {
        location.href = `/ride.html?pickup_id=${p.value}&dest_id=${d.value}&class_id=${b.dataset.c}&pax=2&bags=2`;
      });
    };
  }
  if (tab === "trips") {
    const rows = await VELORA.get("/api/bookings").catch(() => []);
    el.innerHTML = `<h2>Trips</h2>` + (rows.map((b) => `<div class="glass" style="margin:8px 0"><b>${b.id}</b><p class="sub">${b.status}<br/>${b.pickup.name}</p></div>`).join("") || "<p>No trips yet.</p>");
  }
  if (tab === "me") {
    el.innerHTML = `<h2>Me</h2><p class="sub">Apple-light guest profile</p>
      <a class="btn btn-p btn-block" href="/account.html">Sign in</a>
      <p class="sub" style="margin-top:12px">Language ${VELORA.lang} · ${VELORA.currency}</p>`;
  }
}

function paintTabs() {
  document.querySelectorAll(".app-tab button").forEach((b) => b.classList.toggle("on", b.dataset.tab === tab));
}

async function boot() {
  catalog = await VELORA.get("/api/catalog");
  document.querySelectorAll(".app-tab button").forEach((b) => b.onclick = () => { tab = b.dataset.tab; paintTabs(); render(); });
  render();
}
boot();
