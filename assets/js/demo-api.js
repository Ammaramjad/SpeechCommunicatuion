/** Client-side API fallback when VELORA runs on static hosting (e.g. surge.sh). */
window.VELORA_DEMO = {
  catalog: null,
  async load() {
    if (!this.catalog) {
      const r = await fetch("/data/catalog.json");
      this.catalog = await r.json();
    }
    return this.catalog;
  },
  loc(id) {
    return this.catalog.locations.find((l) => l.id === id) || this.catalog.locations[0];
  },
  klass(id) {
    return this.catalog.classes.find((c) => c.id === id) || this.catalog.classes[1];
  },
  quote(body) {
    const pickup = this.loc(body.pickup_id);
    const dest = this.loc(body.dest_id);
    const cl = this.klass(body.class_id || "standard");
    const p = this.catalog.pricing;
    const fx = this.catalog.fx;
    const sym = this.catalog.symbols;
    const key = `${body.pickup_id}|${body.dest_id}`;
    const rev = `${body.dest_id}|${body.pickup_id}`;
    const fixed = this.catalog.fixed_routes[key] || this.catalog.fixed_routes[rev];
    let base = fixed || Math.max(p.min_fare, p.base + 28 * 18);
    base = Math.round(base * cl.mult);
    if (body.service === "hourly") base = Math.round(880 * (body.hours || 4) * cl.mult);
    const airport = pickup.kind === "airport" || dest.kind === "airport" ? p.airport : 0;
    const sub = base + airport;
    const service = Math.round(sub * p.service_fee);
    const total = sub + service;
    const ccy = body.currency || "TWD";
    const conv = (n) => (ccy === "TWD" ? n : Math.max(1, Math.round(n * (fx[ccy] || 1))));
    return {
      currency: ccy, symbol: sym[ccy], km: 28, mins: 45,
      breakdown: { base: conv(base), airport: conv(airport), night: 0, stops: 0, extras: 0, service_fee: conv(service), discount: 0, total: conv(total), tolls: "estimated_included", parking: "separate" },
      twd_total: total, class: cl,
    };
  },
  bookings() {
    return JSON.parse(localStorage.getItem("vl-demo-bookings") || "[]");
  },
  saveBookings(rows) {
    localStorage.setItem("vl-demo-bookings", JSON.stringify(rows));
  },
  ref() {
    const a = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
    let s = "VR-";
    for (let i = 0; i < 6; i++) s += a[Math.floor(Math.random() * a.length)];
    return s;
  },
  fleetRef() {
    const a = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
    let s = "FO-";
    for (let i = 0; i < 6; i++) s += a[Math.floor(Math.random() * a.length)];
    return s;
  },
  async get(path) {
    await this.load();
    if (path === "/api/catalog") return this.catalog;
    if (path === "/api/meta") return { brand: "VELORA", fleet_os: this.catalog.fleet_os, services: ["airport", "p2p", "hourly"] };
    if (path === "/api/admin/metrics") {
      const bs = this.bookings();
      const gmv = bs.reduce((s, b) => s + (b.quote?.twd_total || 0), 0);
      return { bookings: bs.length, pending: 0, active: bs.length, gmv, avg: bs.length ? Math.round(gmv / bs.length) : 0, drivers_online: 6, conversion: 42, fleet_os: this.catalog.fleet_os };
    }
    if (path === "/api/admin/channels") {
      const bs = this.bookings();
      const by = {};
      bs.forEach((b) => { const ch = b.channel || "velora"; by[ch] = (by[ch] || 0) + 1; });
      return { channels: this.catalog.channels, bookings_by_channel: by, gmv_by_channel: by, fleet_jobs_total: bs.length, fleet_jobs_queued: bs.length, fleet_jobs_dispatched: 0, fleet_os: this.catalog.fleet_os, recent_jobs: [] };
    }
    if (path === "/api/fleet/jobs") return [];
    if (path === "/api/bookings") return this.bookings();
    if (path.startsWith("/api/bookings/") && path.endsWith("/live")) {
      const id = path.split("/")[3];
      const b = this.bookings().find((x) => x.id === id);
      if (!b) throw new Error("404");
      return { ...b, live: { headline: "Your driver is 8 minutes away", eta_min: 8, driver_pos: { lat: 25.05, lng: 121.52 }, alerts: b.alerts || [] } };
    }
    if (path.startsWith("/api/bookings/")) {
      const id = path.split("/")[3];
      const b = this.bookings().find((x) => x.id === id);
      if (!b) throw new Error("404");
      return b;
    }
    if (path.startsWith("/api/drivers/")) return { first: "Wei", rating: 4.97, reviews: [], vehicle: "Toyota Camry", plate: "TPE-8801", rides: 300 };
    throw new Error("Not found: " + path);
  },
  async post(path, body) {
    await this.load();
    if (path === "/api/search") {
      const pickup = this.loc(body.pickup_id);
      const dest = this.loc(body.dest_id);
      const results = this.catalog.classes.filter((c) => body.pax <= c.pax).slice(0, 6).map((cl) => {
        const q = this.quote({ ...body, class_id: cl.id });
        return { class: cl, instant: true, free_cancel: true, duration: q.mins, distance: q.km, price: q, popular: true, operator: this.catalog.operators[0] };
      });
      return { pickup, dest, count: results.length, results };
    }
    if (path === "/api/quote") return this.quote(body || {});
    if (path === "/api/bookings") {
      const q = this.quote(body || {});
      const id = this.ref();
      const booking = {
        ...body, id, public_id: id, status: "driver_en_route", payment_status: "paid",
        quote: q, channel: body.channel || "velora", fleet_job_id: this.fleetRef(),
        pickup: this.loc(body.pickup_id), dest: this.loc(body.dest_id),
        driver: { first: "Wei", rating: 4.97, plate: "TPE-8801", model: "Toyota Camry" },
        alerts: [{ type: "driver", text: "Wei is on the way." }],
        created_at: new Date().toISOString(),
      };
      const rows = this.bookings();
      rows.unshift(booking);
      this.saveBookings(rows);
      return booking;
    }
    if (path === "/api/events") return { ok: "tracked" };
    if (path.includes("/ops")) return this.get(path.replace("/ops", ""));
    if (path.includes("/review")) return { verified: true, text: body?.text || "" };
    if (path.includes("/cancel")) return { status: "cancelled" };
    if (path.includes("/assign")) return this.get(path.replace("/assign", ""));
    return { ok: true };
  },
};
