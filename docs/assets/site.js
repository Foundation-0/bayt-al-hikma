/* Bayt al-Hikma site behaviour. Dependency-free.
   Theme (dark, light, auto) and hue persist in localStorage and carry to
   every page, after Eido. Hue is style only. It never encodes a finding.
   Copy buttons copy the command or digest printed beside them. */
(function () {
  "use strict";
  var root = document.documentElement;

  function store(key, value) {
    try { if (value === null) localStorage.removeItem(key); else localStorage.setItem(key, value); } catch (e) {}
  }
  function recall(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }

  var savedHue = parseInt(recall("bayt-hue"), 10);
  if (!isNaN(savedHue) && savedHue >= 0 && savedHue <= 360) {
    root.style.setProperty("--eco-hue", String(savedHue));
  }
  var savedTheme = recall("bayt-theme");
  if (savedTheme === "light" || savedTheme === "dark") {
    root.dataset.theme = savedTheme;
  } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches) {
    root.dataset.theme = "light";
  }

  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    root.classList.add("reduced-motion");
  }

  function currentHue() {
    var v = getComputedStyle(root).getPropertyValue("--eco-hue");
    var n = parseInt(v, 10);
    return isNaN(n) ? 92 : n;
  }

  var hueInput = document.querySelector("[data-hue-input]");
  var hueOut = document.querySelector("[data-hue-out]");
  if (hueInput) {
    hueInput.value = String(currentHue());
    if (hueOut) hueOut.textContent = String(currentHue());
    hueInput.addEventListener("input", function () {
      root.style.setProperty("--eco-hue", hueInput.value);
      if (hueOut) hueOut.textContent = hueInput.value;
      store("bayt-hue", hueInput.value);
    });
  }

  var themeBtn = document.querySelector("[data-theme-btn]");
  function themeLabel() {
    if (!themeBtn) return;
    var t = root.dataset.theme === "light" ? "light" : "dark";
    themeBtn.textContent = t;
    themeBtn.setAttribute("aria-label", "Colour theme: " + t + ". Activate to switch.");
  }
  if (themeBtn) {
    themeLabel();
    themeBtn.addEventListener("click", function () {
      var next = root.dataset.theme === "light" ? "dark" : "light";
      root.dataset.theme = next;
      store("bayt-theme", next);
      themeLabel();
    });
  }

  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var target = document.querySelector(btn.getAttribute("data-copy"));
      var text = target ? target.textContent.trim() : "";
      function done(ok) {
        btn.dataset.state = ok ? "copied" : "";
        btn.textContent = ok ? "Copied" : "Copy failed";
        setTimeout(function () { btn.textContent = "Copy"; btn.dataset.state = ""; }, 2200);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () { done(true); }, function () { done(false); });
      } else {
        var ta = document.createElement("textarea");
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        var ok = false;
        try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
        document.body.removeChild(ta);
        done(ok);
      }
    });
  });
})();
