window.VELORA = {
  lang: localStorage.getItem("vl-lang") || "en",
  currency: localStorage.getItem("vl-ccy") || "TWD",
  token: localStorage.getItem("vl-token") || "",
  user: JSON.parse(localStorage.getItem("vl-user") || "none".replace("none", "null")),
  apiBase: window.VELORA_API_BASE || "",
  staticMode: /\.surge\.sh$/i.test(location.hostname),
  fleet: "https://fleet-dispatch-demo-8c37.surge.sh/",
  publicUrl: "https://velora-private-rides.surge.sh/",
  I18N: {
    en: {
      book: "Book a Ride", airport: "Airport Transfer", hourly: "Hourly Hire", city: "City Transfer",
      bookings: "My Bookings", help: "Help", signin: "Sign in", search: "Search",
      pickup: "Pickup", dest: "Destination", date: "Date", time: "Time", pax: "Passengers", bags: "Luggage",
      hero: "Your private ride, wherever you go.",
      lede: "Book trusted professional drivers for airport transfers, city rides, business travel and private journeys.",
      why: "Why VELORA", popular: "Popular routes", choose: "Choose your ride", how: "How it works",
      faq: "Questions, answered", support: "Support", select: "Select", bookNow: "Book now",
      confirm: "Confirm & Pay", guest: "Continue as guest", terms: "I agree to Terms and Cancellation Policy",
      confirmed: "Booking confirmed", voucher: "Download voucher", track: "Track driver",
    },
    "zh-TW": {
      book: "預訂行程", airport: "機場接送", hourly: "時租包車", city: "市區接送",
      bookings: "我的訂單", help: "協助", signin: "登入", search: "搜尋",
      pickup: "上車", dest: "下車", date: "日期", time: "時間", pax: "人數", bags: "行李",
      hero: "專屬座車，隨行所至。",
      lede: "為機場接送、市區移動與商務出行預約專業司機。",
      why: "為何選擇 VELORA", popular: "熱門路線", choose: "選擇車型", how: "如何預訂",
      faq: "常見問題", support: "客服", select: "選擇", bookNow: "立即預訂",
      confirm: "確認並付款", guest: "以訪客結帳", terms: "我同意條款與取消政策",
      confirmed: "預訂成功", voucher: "下載憑證", track: "追蹤司機",
    },
    "zh-CN": { book: "预订行程", airport: "机场接送", search: "搜索", hero: "专属座驾，随行所至。" },
    ja: { book: "配車を予約", airport: "空港送迎", search: "検索", hero: "専用車が、どこへでも。" },
    ko: { book: "차량 예약", airport: "공항 이동", search: "검색", hero: "프라이빗 라이드, 어디든." },
    ar: { book: "احجز رحلة", airport: "نقل المطار", search: "بحث", hero: "سيارتك الخاصة أينما ذهبت." },
  },
  t(k) {
    const pack = this.I18N[this.lang] || this.I18N.en;
    return pack[k] || this.I18N.en[k] || k;
  },
  async get(path) {
    if (this.staticMode && window.VELORA_DEMO) return VELORA_DEMO.get(path);
    try {
      const r = await fetch(this.apiBase + path, { headers: this.headers() });
      if (!r.ok) throw new Error(await r.text());
      return r.json();
    } catch (err) {
      if (window.VELORA_DEMO) return VELORA_DEMO.get(path);
      throw err;
    }
  },
  async post(path, body) {
    if (this.staticMode && window.VELORA_DEMO) return VELORA_DEMO.post(path, body);
    try {
      const r = await fetch(this.apiBase + path, { method: "POST", headers: { "Content-Type": "application/json", ...this.headers() }, body: JSON.stringify(body || {}) });
      if (!r.ok) throw new Error(await r.text());
      return r.json();
    } catch (err) {
      if (window.VELORA_DEMO) return VELORA_DEMO.post(path, body);
      throw err;
    }
  },
  headers() {
    return this.token ? { Authorization: "Bearer " + this.token } : {};
  },
  money(n, ccy) {
    ccy = ccy || this.currency;
    const map = { TWD: "NT$", USD: "$", EUR: "€", JPY: "¥", KRW: "₩", GBP: "£", AED: "AED ", SAR: "SAR " };
    return map[ccy] + Number(n || 0).toLocaleString();
  },
  track(name, meta) {
    this.post("/api/events", { name, meta: meta || {} }).catch(() => {});
  },
  saveSearch(s) {
    const rows = JSON.parse(localStorage.getItem("vl-recent") || "[]");
    rows.unshift(s);
    localStorage.setItem("vl-recent", JSON.stringify(rows.slice(0, 6)));
  },
  recent() {
    return JSON.parse(localStorage.getItem("vl-recent") || "[]");
  },
};

function headerHTML(active) {
  return `
  <a class="skip" href="#main">Skip to search</a>
  <header class="header">
    <a class="brand" href="/"><span class="mark">V</span> VELORA</a>
    <nav class="nav" aria-label="Primary">
      <a href="/#search" class="${active==="book"?"active":""}">${VELORA.t("book")}</a>
      <a href="/results.html?service=airport">${VELORA.t("airport")}</a>
      <a href="/results.html?service=hourly">${VELORA.t("hourly")}</a>
      <a href="/results.html?service=p2p">${VELORA.t("city")}</a>
      <a href="/results.html?service=p2p">Intercity</a>
      <a href="/help.html#corporate">Corporate</a>
      <a href="/app.html">App</a>
      <a href="/account.html">${VELORA.t("bookings")}</a>
      <a href="/help.html">${VELORA.t("help")}</a>
      <a href="/driver.html">Drivers</a>
      <a href="/admin.html">Ops</a>
      <a href="${VELORA.fleet}" target="_blank" rel="noopener">Fleet OS</a>
    </nav>
    <button class="menu-btn" id="menuBtn" type="button" aria-label="Open menu">Menu</button>
    <div class="tools">
      <select class="chip" id="langSel" aria-label="Language">
        <option value="en">EN</option><option value="zh-TW">繁中</option><option value="zh-CN">简中</option>
        <option value="ja">日本語</option><option value="ko">한국어</option><option value="ar">العربية</option>
      </select>
      <select class="chip" id="ccySel" aria-label="Currency">
        <option>TWD</option><option>USD</option><option>EUR</option><option>JPY</option>
        <option>KRW</option><option>GBP</option><option>AED</option><option>SAR</option>
      </select>
      <a class="chip" href="/help.html">${VELORA.t("support")}</a>
      <a class="btn btn-p" href="/account.html">${VELORA.t("signin")}</a>
    </div>
  </header>
  <div class="nav-drawer" id="navDrawer" hidden>
    <a href="/#search">${VELORA.t("book")}</a>
    <a href="/results.html?service=airport">${VELORA.t("airport")}</a>
    <a href="/results.html?service=hourly">${VELORA.t("hourly")}</a>
    <a href="/results.html?service=p2p">${VELORA.t("city")}</a>
    <a href="/results.html?service=p2p">Intercity</a>
    <a href="/help.html#corporate">Corporate</a>
    <a href="/app.html">App</a>
    <a href="/account.html">${VELORA.t("bookings")}</a>
    <a href="/help.html">${VELORA.t("help")}</a>
    <a href="/driver.html">Drivers</a>
    <a href="/admin.html">Ops</a>
    <a href="${VELORA.fleet}" target="_blank" rel="noopener">Fleet OS</a>
  </div>`;
}

function footerHTML() {
  return `<footer class="footer"><div class="wrap fgrid">
    <div><b>VELORA</b><a href="/help.html">About</a><a href="/help.html">Contact</a><a href="/help.html">Careers</a></div>
    <div><b>Services</b><a href="/results.html?service=airport">Airport Transfer</a><a href="/results.html?service=p2p">City Transfer</a><a href="/results.html?service=hourly">Hourly Hire</a></div>
    <div><b>Partners</b><a href="/driver.html">Driver</a><a href="/admin.html">Operator / Admin</a><a href="/app.html">Customer app</a><a href="${VELORA.fleet}" target="_blank" rel="noopener">Fleet Dispatch</a></div>
    <div><b>Support</b><a href="/help.html">Help Center</a><a href="/help.html#cancel">Cancellation</a><a href="/help.html#terms">Terms</a><a href="/help.html#privacy">Privacy</a></div>
  </div><div class="wrap" style="margin-top:24px;opacity:.7">© VELORA · Private cars with professional drivers · Demo payments never store cards</div></footer>`;
}

function bindChrome() {
  const lang = document.getElementById("langSel");
  const ccy = document.getElementById("ccySel");
  if (lang) { lang.value = VELORA.lang; lang.onchange = () => { VELORA.lang = lang.value; localStorage.setItem("vl-lang", lang.value); document.documentElement.lang = lang.value; document.documentElement.dir = lang.value === "ar" ? "rtl" : "ltr"; location.reload(); }; }
  if (ccy) { ccy.value = VELORA.currency; ccy.onchange = () => { VELORA.currency = ccy.value; localStorage.setItem("vl-ccy", ccy.value); location.reload(); }; }
  const menu = document.getElementById("menuBtn");
  const drawer = document.getElementById("navDrawer");
  if (menu && drawer) {
    menu.onclick = () => {
      const open = drawer.hasAttribute("hidden");
      if (open) drawer.removeAttribute("hidden");
      else drawer.setAttribute("hidden", "");
      menu.setAttribute("aria-expanded", String(open));
    };
  }
}

function locOptions(rows, selected) {
  return rows.map((p) => `<option value="${p.id}" ${p.id===selected?"selected":""}>${p.name}</option>`).join("");
}

function tomorrow() {
  const d = new Date(); d.setDate(d.getDate() + 1); d.setHours(10, 0, 0, 0);
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}
