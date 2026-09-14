/** Detect GitHub Pages subpath and static hosts before other scripts run. */
(function () {
  const host = location.hostname;
  let base = "";
  if (host.endsWith("github.io")) {
    const parts = location.pathname.split("/").filter(Boolean);
    if (parts.length) base = "/" + parts[0];
  }
  window.VELORA_SITE_BASE = base;
  window.VELORA_STATIC_HOST = /\.surge\.sh$/i.test(host) || host.endsWith("github.io");
})();
