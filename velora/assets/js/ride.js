document.getElementById("chrome-header").innerHTML = headerHTML();
document.getElementById("chrome-footer").innerHTML = footerHTML();
bindChrome();
VELORA.track("vehicle_viewed");

const q = Object.fromEntries(new URLSearchParams(location.search));
const form = {
  service: q.service || "airport",
  pickup_id: q.pickup_id || "tpe",
  dest_id: q.dest_id || "taipei-101",
  when: q.when || tomorrow(),
  pax: Number(q.pax || 2),
  bags: Number(q.bags || 2),
  hours: Number(q.hours || 8),
  roundtrip: q.roundtrip === "true",
  class_id: q.class_id || "standard",
  currency: VELORA.currency,
  extras: q.meet === "true" || true ? ["meet"] : [],
  stops: [],
  promo: "",
  first: "Emma", last: "Chen", email: "emma@velora.demo", phone: "+886910000111",
  flight: q.flight || "CI 011", track_flight: true, meet: true, notes: "",
  for_someone: false, passenger_name: "", payment: "card", guest: true, terms: true,
};

let catalog, quote;

async function refreshQuote() {
  quote = await VELORA.post("/api/quote", form);
  document.getElementById("sum").innerHTML = `
    <h3>Price breakdown</h3>
    <p>${quote.class.name}<br/>${form.pickup_id} → ${form.dest_id}</p>
    ${Object.entries(quote.breakdown).filter(([k]) => k !== "total" && k !== "tolls" && k !== "parking").map(([k,v]) => `<div style="display:flex;justify-content:space-between"><span>${k}</span><b>${quote.symbol}${Number(v).toLocaleString()}</b></div>`).join("")}
    <p class="sub">Tolls: ${quote.breakdown.tolls} · Parking: ${quote.breakdown.parking}</p>
    <p class="xl">${quote.symbol}${quote.breakdown.total.toLocaleString()}</p>
    <p class="sub">TOTAL PRICE · per vehicle</p>`;
}

async function boot() {
  catalog = await VELORA.get("/api/catalog");
  const cl = catalog.classes.find((c) => c.id === form.class_id);
  document.getElementById("step1").innerHTML = `
    <h2>${cl.name}</h2>
    <img src="${cl.img}" alt="" style="border-radius:16px;height:220px;width:100%;object-fit:cover"/>
    <p class="sub">${cl.example} · ${cl.pax} passengers · ${cl.bags} bags · AC · ${cl.auto ? "Automatic" : ""}</p>
    <h3>Included</h3><p class="sub">Professional driver, liability cover, bottled water on business+ classes, 45 min airport wait with flight tracking.</p>
    <h3>Excluded</h3><p class="sub">Parking beyond estimate, extra stops unless added, meals.</p>
    <h3>Optional extras</h3>
    ${catalog.extras.map((e) => `<label style="display:block;margin:6px 0"><input type="checkbox" data-ex="${e.id}" ${form.extras.includes(e.id)?"checked":""}/> ${e.name} · ${VELORA.money(e.price,"TWD")}</label>`).join("")}
    <h3>Stops</h3>
    <button class="btn btn-g" type="button" id="addStop">Add stop</button>
    <div id="stopList"></div>
    <label>Promo <input id="promo" placeholder="VELORA10 / AIRPORT200 / NEWGUEST"/></label>
    <p><button class="btn btn-p" id="to2">Continue to passenger</button></p>`;
  document.querySelectorAll("[data-ex]").forEach((c) => c.onchange = () => {
    form.extras = [...document.querySelectorAll("[data-ex]:checked")].map((x) => x.dataset.ex);
    refreshQuote();
  });
  document.getElementById("addStop").onclick = () => {
    const id = prompt("Location id (e.g. ximen, w-hotel, office-nangang)", "ximen");
    if (id) { form.stops.push(id); renderStops(); refreshQuote(); }
  };
  document.getElementById("promo").onchange = () => { form.promo = document.getElementById("promo").value; refreshQuote(); };
  document.getElementById("to2").onclick = () => show(2);
  renderStops();
  document.getElementById("step2").innerHTML = `
    <h2>Passenger</h2>
    <div class="field">First name<input id="first" value="${form.first}"/></div>
    <div class="field">Last name<input id="last" value="${form.last}"/></div>
    <div class="field">Email<input id="email" type="email" value="${form.email}"/></div>
    <div class="field">Phone<input id="phone" value="${form.phone}"/></div>
    <div class="field">WhatsApp (optional)<input id="wa"/></div>
    <div class="field">LINE ID (optional)<input id="line"/></div>
    <div class="field">Flight<input id="flight" value="${form.flight}"/></div>
    <label><input type="checkbox" id="someone"/> I am booking for someone else</label>
    <div class="field hidden" id="paxOther">Passenger name<input id="pname"/></div>
    <div class="field">Notes<textarea id="notes" placeholder="Entrance, child, language"></textarea></div>
    <p><button class="btn btn-p" id="to3">Continue to payment</button></p>`;
  document.getElementById("someone").onchange = (e) => document.getElementById("paxOther").classList.toggle("hidden", !e.target.checked);
  document.getElementById("to3").onclick = () => {
    form.first = first.value; form.last = last.value; form.email = email.value; form.phone = phone.value;
    form.flight = flight.value; form.notes = notes.value; form.for_someone = someone.checked; form.passenger_name = pname.value;
    show(3);
  };
  document.getElementById("step3").innerHTML = `
    <h2>Checkout</h2>
    <p class="sub">Guest checkout is on. Create an account after payment if you wish.</p>
    <div class="field">Payment
      <select id="pay"><option value="card">Card (Stripe / NewebPay abstract)</option><option value="apple">Apple Pay</option><option value="google">Google Pay</option><option value="paypal">PayPal</option></select>
    </div>
    <p class="sub">We authorize a demo payment. Raw card numbers are never stored.</p>
    <label><input type="checkbox" id="terms" checked/> ${VELORA.t("terms")}</label>
    <p><button class="btn btn-p btn-block sticky-cta" id="payBtn">${VELORA.t("confirm")}</button></p>
    <p class="sub" id="err"></p>`;
  document.getElementById("payBtn").onclick = pay;
  await refreshQuote();
}

function renderStops() {
  document.getElementById("stopList").innerHTML = form.stops.map((s, i) => `<div>${i + 1}. ${s} <button type="button" data-rm="${i}">remove</button></div>`).join("");
  document.querySelectorAll("[data-rm]").forEach((b) => b.onclick = () => { form.stops.splice(Number(b.dataset.rm), 1); renderStops(); refreshQuote(); });
}

function show(n) {
  [1, 2, 3].forEach((i) => document.getElementById("step" + i).classList.toggle("hidden", i !== n));
  document.getElementById("s2").classList.toggle("on", n >= 2);
  document.getElementById("s3").classList.toggle("on", n >= 3);
  VELORA.track(n === 3 ? "checkout_started" : "vehicle_selected");
}

async function pay() {
  form.terms = document.getElementById("terms").checked;
  form.payment = document.getElementById("pay").value;
  if (!form.terms) { document.getElementById("err").textContent = "Please accept terms."; return; }
  try {
    VELORA.track("payment_attempted");
    const b = await VELORA.post("/api/bookings", form);
    VELORA.track("booking_completed", { id: b.id });
    location.href = "/confirm.html?id=" + encodeURIComponent(b.id);
  } catch (e) {
    document.getElementById("err").textContent = "Payment unsuccessful. Try another method.";
  }
}

boot();
