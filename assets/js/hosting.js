/** Detect public static hosts (GitHub Pages, Surge) and set asset/API base path. */
(function () {
  const host = location.hostname;
  let base = "";
  if (host.endsWith("github.io")) {
    const parts = location.pathname.split("/").filter(Boolean);
    if (parts.length) base = "/" + parts[0];
  }
  window.VELORA_SITE_BASE = base;
  window.VELORA_STATIC_HOST = /\.surge\.sh$/i.test(host) || host.endsWith("github.io");
  if (base) {
    const el = document.createElement("base");
    el.href = base + "/";
    document.head.prepend(el);
  }
})();
