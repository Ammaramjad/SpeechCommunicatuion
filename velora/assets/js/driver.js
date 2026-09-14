document.getElementById("chrome-header").innerHTML = headerHTML();
document.getElementById("chrome-footer").innerHTML = footerHTML();
bindChrome();
const DID = "d01";

async function render() {
  const jobs = await VELORA.get("/api/bookings");
  const drivers = await VELORA.get("/api/drivers");
  const me = drivers.find((d) => d.id === DID);
  const mine = jobs.filter((b) => b.driver_id === DID || (!b.driver_id && b.status === "payment_confirmed"));
  document.getElementById("root").innerHTML = `
    <h1>Today’s jobs</h1>
    <p>${me.first} · ${me.status} · ★ ${me.rating}
      <button class="chip" id="tog">${me.status === "online" ? "Go offline" : "Go online"}</button>
    </p>
    ${mine.map((b) => `<article class="panel" style="margin:12px 0">
      <span class="status">${b.status}</span> <b>${b.id}</b>
      <p>${b.pickup.name} → ${b.dest.name}</p>
      <p>${b.pax} pax · ${b.bags} bags · flight ${b.flight || "—"} · OTP ${b.otp}</p>
      <p>${b.notes || ""}</p>
      ${!b.driver_id ? `<button class="btn btn-p" data-a="${b.id}">Accept</button>` : ""}
        ${b.driver_id === DID ? `
        <button class="btn btn-g" data-s="${b.id}" data-st="driver_en_route">En route</button>
        <button class="btn btn-g" data-s="${b.id}" data-st="driver_arrived">Arrived</button>
        <button class="btn btn-g" data-s="${b.id}" data-st="on_board">On board</button>
        <button class="btn btn-p" data-s="${b.id}" data-st="trip_completed">Complete</button>
        <button class="btn btn-g" data-ops="${b.id}" data-k="driver_late">I’m delayed</button>
        <button class="btn btn-g" data-ops="${b.id}" data-k="incident">Accident — send replacement</button>` : ""}
    </article>`).join("") || "<p>No jobs in queue.</p>"}
    <p class="sub">Documents: license / insurance — pending review in admin (demo).</p>`;
  document.getElementById("tog").onclick = async () => { await VELORA.post("/api/drivers/" + DID + "/toggle", {}); render(); };
  document.querySelectorAll("[data-a]").forEach((b) => b.onclick = async () => { await VELORA.post("/api/bookings/" + b.dataset.a + "/assign", { driver_id: DID }); render(); });
  document.querySelectorAll("[data-s]").forEach((b) => b.onclick = async () => { await VELORA.post("/api/bookings/" + b.dataset.s + "/status", { status: b.dataset.st }); render(); });
  document.querySelectorAll("[data-ops]").forEach((b) => b.onclick = async () => { await VELORA.post("/api/bookings/" + b.dataset.ops + "/ops", { kind: b.dataset.k, note: "driver portal" }); render(); });
}
render();
