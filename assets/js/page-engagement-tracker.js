(function () {
  "use strict";

  if (window.__trxPageEngagementTrackerLoaded) return;
  window.__trxPageEngagementTrackerLoaded = true;

  if (window.top && window.top !== window.self) return;
  if (!window.location || !window.document) return;

  var TRACK_URL = "/api/analytics/page-track";
  var HEARTBEAT_MS = 15000;
  var ACTIVE_WINDOW_MS = 15000;
  var INDEX_READ_SCROLL_MIN = 8;
  var MAX_SECONDS_LIMIT = 86400 * 1000;

  function nowMs() {
    return Date.now();
  }

  function clamp(value, min, max) {
    var n = Number(value || 0);
    if (!Number.isFinite(n)) return min;
    return Math.max(min, Math.min(max, n));
  }

  function toPath(value) {
    var raw = String(value || "").trim();
    if (!raw) return "/";
    if (raw.indexOf("http://") === 0 || raw.indexOf("https://") === 0) {
      try {
        raw = new URL(raw).pathname || "/";
      } catch (_) {
        raw = "/";
      }
    }
    if (!raw) raw = "/";
    if (raw.charAt(0) !== "/") raw = "/" + raw;
    return raw.slice(0, 220);
  }

  function generateVisitId() {
    var randA = Math.random().toString(36).slice(2, 10);
    var randB = Math.random().toString(36).slice(2, 10);
    var ts = nowMs().toString(36);
    return ("pv_" + ts + "_" + randA + randB).slice(0, 120);
  }

  function getScrollPercent() {
    var doc = document.documentElement || document.body;
    if (!doc) return 0;
    var scrollTop = window.pageYOffset || doc.scrollTop || 0;
    var max = Math.max(1, (doc.scrollHeight || 1) - (window.innerHeight || 0));
    var pct = (scrollTop / max) * 100;
    return Math.round(clamp(pct, 0, 100));
  }

  function parseUtm() {
    var params = new URLSearchParams(window.location.search || "");
    return {
      utm_source: (params.get("utm_source") || "").slice(0, 120),
      utm_medium: (params.get("utm_medium") || "").slice(0, 120),
      utm_campaign: (params.get("utm_campaign") || "").slice(0, 120),
      utm_content: (params.get("utm_content") || "").slice(0, 120),
      utm_term: (params.get("utm_term") || "").slice(0, 120)
    };
  }

  var pathname = toPath(window.location.pathname || "/");
  var isIndex = pathname === "/";
  var visitId = generateVisitId();
  var startAt = nowMs();
  var lastTickAt = startAt;
  var lastInteractionAt = startAt;
  var totalDurationMs = 0;
  var totalActiveMs = 0;
  var totalReadMs = 0;
  var maxScrollPercent = getScrollPercent();
  var navHint = "";
  var finalSent = false;
  var utm = parseUtm();

  function markInteraction() {
    lastInteractionAt = nowMs();
    maxScrollPercent = Math.max(maxScrollPercent, getScrollPercent());
  }

  function updateCounters() {
    var current = nowMs();
    var delta = current - lastTickAt;
    if (delta <= 0) return;

    totalDurationMs = clamp(current - startAt, 0, MAX_SECONDS_LIMIT);
    var visible = document.visibilityState !== "hidden";
    var active = visible && (current - lastInteractionAt) <= ACTIVE_WINDOW_MS;

    if (active) {
      totalActiveMs = clamp(totalActiveMs + delta, 0, MAX_SECONDS_LIMIT);
    }

    if (isIndex && active) {
      var scrollNow = getScrollPercent();
      if (scrollNow >= INDEX_READ_SCROLL_MIN) {
        totalReadMs = clamp(totalReadMs + delta, 0, MAX_SECONDS_LIMIT);
      }
    }

    maxScrollPercent = Math.max(maxScrollPercent, getScrollPercent());
    lastTickAt = current;
  }

  function sendPayload(eventType, isExit, exitType) {
    if (finalSent && isExit) return;

    updateCounters();
    var payload = {
      visit_id: visitId,
      path: pathname,
      page_title: String(document.title || "").slice(0, 200),
      event_type: String(eventType || "heartbeat").slice(0, 32),
      is_exit: Boolean(isExit),
      exit_type: String(exitType || "unknown").slice(0, 40),
      duration_ms: Math.round(totalDurationMs),
      active_ms: Math.round(totalActiveMs),
      read_ms: Math.round(totalReadMs),
      max_scroll_percent: Math.round(clamp(maxScrollPercent, 0, 100)),
      utm_source: utm.utm_source,
      utm_medium: utm.utm_medium,
      utm_campaign: utm.utm_campaign,
      utm_content: utm.utm_content,
      utm_term: utm.utm_term
    };

    var body = JSON.stringify(payload);

    try {
      if (navigator.sendBeacon && typeof Blob !== "undefined") {
        var blob = new Blob([body], { type: "application/json" });
        var ok = navigator.sendBeacon(TRACK_URL, blob);
        if (ok && isExit) finalSent = true;
        if (ok) return;
      }
    } catch (_) {}

    fetch(TRACK_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      keepalive: true,
      body: body
    }).catch(function () { return null; });

    if (isExit) finalSent = true;
  }

  function markNavHintFromLink(anchor) {
    if (!anchor || !anchor.href) return;
    try {
      var url = new URL(anchor.href, window.location.href);
      navHint = (url.origin === window.location.origin) ? "internal" : "outbound";
    } catch (_) {
      navHint = "unknown";
    }
  }

  function markNavHintFromForm(form) {
    if (!form) return;
    var action = String(form.getAttribute("action") || "").trim();
    if (!action) {
      navHint = "internal";
      return;
    }
    try {
      var url = new URL(action, window.location.href);
      navHint = (url.origin === window.location.origin) ? "internal" : "outbound";
    } catch (_) {
      navHint = "unknown";
    }
  }

  function resolveExitType() {
    if (navHint === "internal") return "internal";
    if (navHint === "outbound") return "outbound";
    if (navHint === "reload") return "reload";
    return "close";
  }

  function flushFinal() {
    if (finalSent) return;
    sendPayload("leave", true, resolveExitType());
  }

  ["mousemove", "mousedown", "keydown", "touchstart", "pointerdown", "scroll"].forEach(function (eventName) {
    window.addEventListener(eventName, markInteraction, { passive: true });
  });

  document.addEventListener("click", function (event) {
    var el = event.target;
    if (!el || !el.closest) return;
    var anchor = el.closest("a[href]");
    if (anchor) markNavHintFromLink(anchor);
  }, true);

  document.addEventListener("submit", function (event) {
    markNavHintFromForm(event.target);
  }, true);

  document.addEventListener("visibilitychange", function () {
    updateCounters();
    if (document.visibilityState === "hidden") {
      sendPayload("heartbeat", false, "unknown");
    } else {
      markInteraction();
    }
  });

  window.addEventListener("beforeunload", flushFinal);
  window.addEventListener("pagehide", function () {
    flushFinal();
  });

  window.addEventListener("keydown", function (event) {
    if (event.key === "F5" || ((event.ctrlKey || event.metaKey) && String(event.key || "").toLowerCase() === "r")) {
      navHint = "reload";
    }
  }, true);

  setTimeout(function () {
    sendPayload("view", false, "unknown");
  }, 900);

  setInterval(function () {
    if (finalSent) return;
    if (document.visibilityState === "hidden") return;
    sendPayload("heartbeat", false, "unknown");
  }, HEARTBEAT_MS);
})();

