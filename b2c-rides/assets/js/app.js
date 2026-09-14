const S = { tab: "home", catalog: null, type: "airport_pickup", form: null, booking: null };

function t10() {
  const d = new Date(); d.setDate(d.getDate() + 1); d.setHours(10, 0, 0, 0);
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}

function place(id) { return S.catalog.places.find((p) => p.id === id); }

function shell(inner) {
  document.getElementById("appBody").innerHTML = inner;
  document.querySelectorAll(".app-tab button").forEach((b) => b.classList.toggle("on", b.dataset.tab === S.tab));
}

async function render() {
  document.getElementById("appTitle").textContent = RL.t(S.tab === "home" ? "hero" : S.tab);
  if (S.tab === "home") {
    shell(`
      <div style="padding:12px"><input id="q" placeholder="${RL.t("where")}" style="width:100%;padding:12px;border-radius:12px;border:0"/></div>
      <div class="icons">
        ${[["airport_pickup","pickup","✈️"],["airport_drop","drop","🛫"],["p2p","p2p","🚗"],["hourly","hourly","⏱️"],["rental","rental","🔑"],["instant","taxi","🚕"]].map(([id,k,i]) =>
          `<button class="ico" data-type="${id}"><span>${i}</span>${RL.t(k)}</button>`).join("")}
      </div>
      <div style="padding:0 12px 16px">
        <h3>${RL.t("popular")}</h3>
        ${S.catalog.routes.slice(0,4).map((r) => {
          const a = place(r.from), b = place(r.to);
          return `<div class="card" data-r="${r.id}" style="margin-bottom:10px;display:grid;grid-template-columns:88px 1fr">
            <img src="${r.img}" style="height:88px;object-fit:cover"/>
            <div class="pad"><b>${RL.loc(a)} → ${RL.loc(b)}</b><div class="price">${RL.nt(r.from_price)} 起</div></div></div>`;
        }).join("")}
      </div>`);
    document.querySelectorAll("[data-type]").forEach((b) => b.onclick = () => { S.type = b.dataset.type; S.tab = S.type === "instant" ? "taxi" : "book"; render(); });
    document.querySelectorAll("[data-r]").forEach((el) => el.onclick = () => {
      const r = S.catalog.routes.find((x) => x.id === el.dataset.r);
      S.form.from_id = r.from; S.form.to_id = r.to; S.type = "airport_pickup"; S.tab = "book"; render();
    });
  }

  if (S.tab === "book") {
    const list = S.type === "rental" ? S.catalog.rentals : S.catalog.vehicles;
    let html = `<div style="padding:12px">
      <select data-k="from_id">${S.catalog.places.map((p)=>`<option value="${p.id}" ${p.id===S.form.from_id?"selected":""}>${RL.loc(p)}</option>`).join("")}</select>
      <select data-k="to_id" style="margin-top:8px">${S.catalog.places.map((p)=>`<option value="${p.id}" ${p.id===S.form.to_id?"selected":""}>${RL.loc(p)}</option>`).join("")}</select>
    </div><div id="cars" style="padding:0 12px 20px"></div>`;
    shell(html);
    document.querySelectorAll("[data-k]").forEach((el) => el.onchange = () => { S.form[el.dataset.k] = el.value; });
    const box = document.getElementById("cars");
    for (const v of list) {
      const q = await API.post("/api/quote", { ...S.form, type: S.type, vehicle_id: v.id });
      box.insertAdjacentHTML("beforeend", `<div class="card" style="margin-bottom:10px">
        <img src="${v.img}" style="height:110px;object-fit:cover"/>
        <div class="pad"><b>${RL.car(v)}</b><div class="price">${RL.nt(q.fare.total)}</div>
        <button class="btn btn-k btn-block" data-vid="${v.id}">${RL.t("book")}</button></div></div>`);
    }
    box.querySelectorAll("[data-vid]").forEach((b) => b.onclick = async () => {
      S.booking = await API.post("/api/bookings", { ...S.form, type: S.type, vehicle_id: b.dataset.vid, channel: "app" });
      S.tab = "done"; render();
    });
  }

  if (S.tab === "taxi") {
    shell(`<div style="padding:12px"><h3>${RL.t("where")}</h3>
      <p class="sub">${RL.loc(place(S.form.from_id))} → ${RL.loc(place(S.form.to_id))}</p>
      <div id="tx"></div></div>`);
    const box = document.getElementById("tx");
    for (const v of S.catalog.taxi_classes) {
      const q = await API.post("/api/quote", { ...S.form, type: "instant", vehicle_id: v.id });
      box.insertAdjacentHTML("beforeend", `<button class="btn btn-ghost btn-block" data-vid="${v.id}" style="margin:8px 0;justify-content:space-between;display:flex">
        ${RL.car(v)} · ETA ${v.eta}m <b>${RL.nt(q.fare.total)}</b></button>`);
    }
    box.querySelectorAll("[data-vid]").forEach((b) => b.onclick = async () => {
      S.booking = await API.post("/api/bookings", { ...S.form, type: "instant", vehicle_id: b.dataset.vid, channel: "app" });
      S.tab = "done"; render();
    });
  }

  if (S.tab === "done") {
    const b = S.booking;
    shell(`<div class="pad" style="padding:20px">
      <h2>${RL.t("confirm")}</h2>
      <div class="voucher"><b>${b.id}</b><p>${RL.loc(b.from_place)} → ${RL.loc(b.to_place)}</p>
      <p>${RL.t("otp")} ${b.otp}</p><p>${RL.nt(b.fare.total)}</p>
      <p>channel: app</p></div></div>`);
  }

  if (S.tab === "bookings") {
    const rows = await API.get("/api/bookings?channel=app");
    const all = await API.get("/api/bookings");
    shell(`<div class="pad" style="padding:12px"><h3>${RL.t("bookings")}</h3>
      ${all.filter((b)=>b.channel==="app"||b.channel==="web").map((b)=>`<div class="card" style="margin:8px 0"><div class="pad">
        <b>${b.id}</b> · ${b.channel} · ${b.status}<div class="price">${RL.nt(b.fare.total)}</div>
        <div class="sub">${RL.loc(b.from_place)} → ${RL.loc(b.to_place)}</div></div></div>`).join("") || "<p>—</p>"}</div>`);
  }

  if (S.tab === "account") {
    shell(`<div class="pad" style="padding:16px">
      <h3>${RL.t("account")}</h3>
      <p>林小華 · 0912-000-888</p>
      <p>Wallet · NT$ 350 折價金</p>
      <p>Language: ${RL.lang}</p>
      <button class="btn btn-ghost" id="lg">${RL.t("lang")}</button>
      <p class="sub" style="margin-top:12px">${RL.t("support")}: 24h chat demo</p>
    </div>`);
    document.getElementById("lg").onclick = () => RL.toggle();
  }
}

async function boot() {
  S.catalog = await API.get("/api/catalog");
  S.form = { from_id: "tpe", to_id: "xinyi", when: t10(), pax: 2, bags: 2, hours: 8, days: 2, meet: true, child_seat: false, english: true, pet: false, promo: "TPE200", name: "林小華", phone: "0912-000-888", flight: "BR 071", channel: "app" };
  document.querySelectorAll(".app-tab button").forEach((b) => {
    const icons = { home: "🏠", book: "🔎", bookings: "🧾", account: "👤" };
    const keys = { home: "home", book: "search", bookings: "bookings", account: "account" };
    b.innerHTML = `${icons[b.dataset.tab]}<br/>${RL.t(keys[b.dataset.tab])}`;
    b.onclick = () => { S.tab = b.dataset.tab; render(); };
  });
  document.getElementById("langBtn").onclick = () => RL.toggle();
  render();
}
boot();
