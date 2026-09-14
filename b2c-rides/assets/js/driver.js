const DID = localStorage.getItem("rl-driver") || "d1";
let catalog;

async function render() {
  const drivers = await API.get("/api/drivers");
  const me = drivers.find((d) => d.id === DID) || drivers[0];
  localStorage.setItem("rl-driver", me.id);
  const jobs = await API.get("/api/bookings");
  const mine = jobs.filter((b) => b.driver_id === me.id && !["completed","cancelled"].includes(b.status));
  const incoming = jobs.filter((b) => b.status === "new");
  document.getElementById("drvHead").textContent = `${me.name} · ${me.plate} · ${me.status}`;
  document.getElementById("drvBody").innerHTML = `
    <div class="pad">
      <label>切換司機
        <select id="who">${drivers.map((d)=>`<option value="${d.id}" ${d.id===me.id?"selected":""}>${d.name} (${d.plate})</option>`).join("")}</select>
      </label>
      <p><button class="btn btn-ghost" id="tog">${me.status === "offline" ? RL.t("online") : RL.t("offline")}</button></p>
      <h3>進行中</h3>
      ${mine.map((b)=>`<div class="card"><div class="pad">
        <b>${b.id}</b> · ${b.status}<p>${RL.loc(b.from_place)} → ${RL.loc(b.to_place)}</p>
        <p>${RL.t("otp")} ${b.otp} · ${RL.nt(b.fare.total)}</p>
        ${b.status==="assigned"?`<button class="btn btn-k" data-s="accepted" data-id="${b.id}">${RL.t("accept")}</button>`:""}
        ${b.status==="accepted"?`<button class="btn btn-k" data-s="arriving" data-id="${b.id}">${RL.t("arriving")}</button>`:""}
        ${b.status==="arriving"?`<button class="btn btn-k" data-s="onboard" data-id="${b.id}">${RL.t("onboard")}</button>`:""}
        ${b.status==="onboard"?`<button class="btn btn-k" data-s="completed" data-id="${b.id}">${RL.t("complete")}</button>`:""}
      </div></div>`).join("") || "<p>—</p>"}
      <h3>待派遣</h3>
      ${incoming.map((b)=>`<div class="card"><div class="pad">
        <b>${b.id}</b> ${b.channel}<p>${RL.loc(b.from_place)} → ${RL.loc(b.to_place)}</p>
        <button class="btn btn-k" data-claim="${b.id}">${RL.t("accept")}</button>
      </div></div>`).join("") || "<p>—</p>"}
    </div>`;
  document.getElementById("who").onchange = (e) => { localStorage.setItem("rl-driver", e.target.value); render(); };
  document.getElementById("tog").onclick = async () => { await API.post(`/api/drivers/${me.id}/toggle`, {}); render(); };
  document.querySelectorAll("[data-s]").forEach((b) => b.onclick = async () => {
    await API.post(`/api/bookings/${b.dataset.id}/status`, { status: b.dataset.s });
    render();
  });
  document.querySelectorAll("[data-claim]").forEach((b) => b.onclick = async () => {
    await API.post(`/api/bookings/${b.dataset.claim}/assign`, { driver_id: me.id });
    render();
  });
}

async function boot() {
  catalog = await API.get("/api/catalog");
  document.getElementById("langBtn").onclick = () => RL.toggle();
  render();
  setInterval(render, 4000);
}
boot();
