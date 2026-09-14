const state = {
  from: "DEL — Indira Gandhi Airport",
  to: "Connaught Place, Delhi",
  when: "",
  pax: "2",
  mode: "pickup",
  car: null,
  bookingId: "",
};

function show(id) {
  ["home", "results", "detail", "checkout", "done"].forEach((v) => {
    document.getElementById("view-" + v).classList.toggle("hidden", v !== id);
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function applyCopy() {
  document.getElementById("langBtn").onclick = () => RideLook.toggleLang();
  document.getElementById("hero").textContent = RideLook.t("hero");
  document.getElementById("heroSub").textContent = RideLook.t("heroSub");
  document.getElementById("searchBtn").textContent = RideLook.t("search");
  document.getElementById("popular").textContent = RideLook.t("popular");
  document.getElementById("why").textContent = RideLook.t("why");
  document.getElementById("resultsTitle").textContent = RideLook.t("results");
  document.getElementById("bookBtn").textContent = RideLook.t("book");
  document.getElementById("payBtn").textContent = RideLook.t("pay");
  document.getElementById("doneTitle").textContent = RideLook.t("done");
}

function fillPlaces() {
  const dl = document.getElementById("places");
  RIDEDATA.places.forEach((p) => {
    const o = document.createElement("option");
    o.value = p;
    dl.appendChild(o);
  });
}

function routeCards() {
  const root = document.getElementById("routeCards");
  root.innerHTML = RIDEDATA.routes.map((r) => `
    <article class="card" data-route="${r.id}">
      <img src="${r.img}" alt="" />
      <div class="card-body">
        <span class="badge">${r.mins} min</span>
        <h3>${r.from.split("—")[0].trim()} → ${r.to.split(",")[0]}</h3>
        <p class="meta">${r.from}<br/>${r.to}</p>
        <div class="price">From ${RideLook.inr(r.fromPrice)}</div>
      </div>
    </article>
  `).join("");
  root.querySelectorAll("[data-route]").forEach((el) => {
    el.onclick = () => {
      const r = RIDEDATA.routes.find((x) => x.id === el.dataset.route);
      state.from = r.from;
      state.to = r.to;
      document.querySelector('[name="from"]').value = r.from;
      document.querySelector('[name="to"]').value = r.to;
      renderResults();
      show("results");
    };
  });
}

function filteredCars() {
  const types = [...document.querySelectorAll(".ftype:checked")].map((x) => x.value);
  const meet = document.getElementById("meetOnly").checked;
  return RIDEDATA.cars.filter((c) => types.includes(c.type) && (!meet || c.meet));
}

function renderResults() {
  document.getElementById("tripSummary").textContent =
    `${state.from} → ${state.to} · ${state.pax} passengers`;
  const list = document.getElementById("resultList");
  const cars = filteredCars();
  list.innerHTML = cars.map((c) => `
    <article class="result">
      <img src="${c.img}" alt="${c.name}" />
      <div>
        <h3>${c.name}</h3>
        <p class="stars">★ ${c.rating} (${c.reviews.toLocaleString()})</p>
        <p class="meta">${c.seats} seats · ${c.bags} bags · ${c.amenities.join(" · ")}</p>
      </div>
      <div class="result-price">
        <div><s>${RideLook.inr(c.old)}</s></div>
        <div class="amt">${RideLook.inr(c.price)}</div>
        <button class="btn btn-orange" type="button" data-car="${c.id}">${RideLook.t("book")}</button>
      </div>
    </article>
  `).join("");
  list.querySelectorAll("[data-car]").forEach((btn) => {
    btn.onclick = () => openCar(btn.dataset.car);
  });
}

function openCar(id) {
  state.car = RIDEDATA.cars.find((c) => c.id === id);
  const c = state.car;
  document.getElementById("dImg").src = c.img;
  document.getElementById("dName").textContent = c.name;
  document.getElementById("dStars").textContent = `★ ${c.rating} · ${c.reviews} reviews`;
  document.getElementById("dPrice").textContent = RideLook.inr(c.price);
  document.getElementById("dTrip").textContent = `${state.from} → ${state.to}`;
  document.getElementById("dChips").innerHTML = c.amenities.map((a) => `<span class="chip">${a}</span>`).join("");
  show("detail");
}

function orderBox() {
  const c = state.car;
  document.getElementById("orderBox").innerHTML = `
    <h3>Trip summary</h3>
    <p class="meta">${state.from}<br/>→ ${state.to}</p>
    <p><strong>${c.name}</strong></p>
    <p class="amt">${RideLook.inr(c.price)}</p>
  `;
}

function initWhen() {
  const el = document.querySelector('[name="when"]');
  const d = new Date();
  d.setDate(d.getDate() + 1);
  d.setHours(10, 0, 0, 0);
  const pad = (n) => String(n).padStart(2, "0");
  el.value = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  state.when = el.value;
}

document.getElementById("modeTabs").onclick = (e) => {
  const tab = e.target.closest(".tab");
  if (!tab) return;
  document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
  tab.classList.add("active");
  state.mode = tab.dataset.mode;
};

document.getElementById("searchForm").onsubmit = (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  state.from = fd.get("from");
  state.to = fd.get("to");
  state.when = fd.get("when");
  state.pax = fd.get("pax");
  renderResults();
  show("results");
};

document.querySelectorAll("[data-go]").forEach((el) => {
  el.addEventListener("click", (ev) => {
    ev.preventDefault();
    const v = el.dataset.go;
    if (v === "results") renderResults();
    show(v);
  });
});

document.querySelectorAll(".ftype, #meetOnly").forEach((el) => {
  el.addEventListener("change", renderResults);
});

document.getElementById("bookBtn").onclick = () => {
  orderBox();
  show("checkout");
};

document.getElementById("payForm").onsubmit = (e) => {
  e.preventDefault();
  state.bookingId = "RL-" + Math.floor(100000 + Math.random() * 900000);
  document.getElementById("doneMeta").textContent =
    `Booking ${state.bookingId} · ${state.car.name} · ${RideLook.inr(state.car.price)}`;
  show("done");
};

applyCopy();
fillPlaces();
routeCards();
initWhen();
