document.getElementById("chrome-header").innerHTML = headerHTML("bookings");
document.getElementById("chrome-footer").innerHTML = footerHTML();
bindChrome();
const root = document.getElementById("main");

function loginForm() {
  root.innerHTML = `<div class="two">
    <form class="panel" id="login">
      <h2>Sign in</h2>
      <div class="field">Email<input name="email" value="emma@velora.demo"/></div>
      <div class="field">Password<input name="password" type="password" value="demo"/></div>
      <button class="btn btn-p" type="submit">Sign in</button>
      <p class="sub">Demo: emma@velora.demo / driver@velora.demo / admin@velora.demo — password demo</p>
      <p><button class="btn btn-g" type="button" id="google">Continue with Google (demo)</button>
         <button class="btn btn-g" type="button" id="apple">Continue with Apple (demo)</button></p>
    </form>
    <form class="panel" id="guest">
      <h2>Find a guest booking</h2>
      <div class="field">Reference<input name="id" placeholder="VR-XXXXXX"/></div>
      <div class="field">Email<input name="email" placeholder="used at checkout"/></div>
      <button class="btn btn-p" type="submit">Retrieve</button>
    </form>
  </div>`;
  document.getElementById("login").onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      const res = await VELORA.post("/api/auth/login", { email: fd.get("email"), password: fd.get("password") });
      VELORA.token = res.token; VELORA.user = res.user;
      localStorage.setItem("vl-token", res.token); localStorage.setItem("vl-user", JSON.stringify(res.user));
      if (res.user.role === "admin" || res.user.role === "dispatcher") location.href = "/admin.html";
      else if (res.user.role === "driver") location.href = "/driver.html";
      else dash();
    } catch { alert("Invalid credentials"); }
  };
  document.getElementById("google").onclick = () => document.getElementById("login").requestSubmit();
  document.getElementById("apple").onclick = () => document.getElementById("login").requestSubmit();
  document.getElementById("guest").onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    location.href = "/confirm.html?id=" + encodeURIComponent(fd.get("id"));
  };
}

async function dash() {
  const rows = await VELORA.get("/api/bookings");
  root.innerHTML = `<h1>Hello ${VELORA.user.name}</h1>
    <p><button class="chip" id="out">Sign out</button> · Credits NT$ 0 · Points 0 (loyalty flag off)</p>
    <h2>Bookings</h2>
    ${rows.map((b) => `<article class="result" style="grid-template-columns:1fr auto">
      <div><span class="status">${b.status}</span> <b>${b.id}</b><br/>${b.pickup.name} → ${b.dest.name}<br/>${b.class.name}</div>
      <div>
        <div class="price">${b.quote.symbol}${b.quote.breakdown.total.toLocaleString()}</div>
        <a class="btn btn-p" href="/track.html?id=${encodeURIComponent(b.id)}">Track</a>
        <a class="btn btn-g" href="/app.html?id=${encodeURIComponent(b.id)}">App</a>
        <a class="btn btn-g" href="/results.html?pickup_id=${b.pickup_id}&dest_id=${b.dest_id}&pax=${b.pax}&bags=${b.bags}">Book again</a>
        ${!["trip_completed","cancelled"].includes(b.status) ? `<button class="btn btn-g" data-c="${b.id}">Cancel</button>` : ""}
      </div></article>`).join("") || "<p>No bookings yet.</p>"}
    <h2>Saved addresses</h2><p class="sub">Home / Office / Hotel — add from a completed trip.</p>
    <h2>Support</h2><a class="btn btn-p" href="/help.html">Open a ticket</a>`;
  document.getElementById("out").onclick = () => { localStorage.removeItem("vl-token"); localStorage.removeItem("vl-user"); location.reload(); };
  document.querySelectorAll("[data-c]").forEach((b) => b.onclick = async () => { await VELORA.post("/api/bookings/" + b.dataset.c + "/cancel", {}); dash(); });
}

if (VELORA.token && VELORA.user) dash(); else loginForm();
