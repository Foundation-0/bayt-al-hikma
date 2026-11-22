/* Live figures. Nothing here is a picture of a result computed elsewhere.
   Each figure draws from the numbers printed beside it in the page, and
   those numbers come from the committed certificates. If JavaScript is
   off, the tables beside each figure still carry every value. */
(function () {
  "use strict";
  var root = document.documentElement;
  var reduced = root.classList.contains("reduced-motion") ||
    (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);

  function cssColor(name) {
    return getComputedStyle(root).getPropertyValue(name).trim() || "#dbc69a";
  }

  /* Opening pattern: six circles round one, after the belief page, inside
     a hexagon. Nine points on the outer ring count the nine pinned texts.
     Slow rotation carries no quantity and stops under reduced motion. */
  var pat = document.querySelector("[data-pattern]");
  if (pat && pat.getContext) {
    var pctx = pat.getContext("2d");
    var S = 640;
    pat.width = S; pat.height = S;
    var t0 = 0;
    function drawPattern(t) {
      var cx = S / 2, cy = S / 2;
      var R = S * 0.352, r = S * 0.176;
      var rot = reduced ? 0 : (t * 0.00002) % (Math.PI * 2);
      var gold = cssColor("--accent"), data = cssColor("--data"), ink = cssColor("--ink");
      pctx.clearRect(0, 0, S, S);
      var g = pctx.createRadialGradient(cx, cy, 10, cx, cy, S * 0.48);
      g.addColorStop(0, gold);
      g.addColorStop(1, "transparent");
      pctx.save();
      pctx.globalAlpha = 0.1;
      pctx.fillStyle = g;
      pctx.beginPath(); pctx.arc(cx, cy, S * 0.48, 0, Math.PI * 2); pctx.fill();
      pctx.restore();
      pctx.strokeStyle = gold; pctx.lineWidth = 1.2; pctx.globalAlpha = 0.55;
      pctx.beginPath(); pctx.arc(cx, cy, R, 0, Math.PI * 2); pctx.stroke();
      pctx.beginPath(); pctx.arc(cx, cy, r, 0, Math.PI * 2); pctx.stroke();
      for (var i = 0; i < 6; i++) {
        var a = rot + i * Math.PI / 3 - Math.PI / 2;
        var x = cx + Math.cos(a) * r, y = cy + Math.sin(a) * r;
        pctx.beginPath(); pctx.arc(x, y, r, 0, Math.PI * 2); pctx.stroke();
      }
      pctx.globalAlpha = 0.45;
      pctx.beginPath();
      for (var j = 0; j < 6; j++) {
        var ha = rot + j * Math.PI / 3 - Math.PI / 2;
        var hx = cx + Math.cos(ha) * R, hy = cy + Math.sin(ha) * R;
        if (j === 0) pctx.moveTo(hx, hy); else pctx.lineTo(hx, hy);
      }
      pctx.closePath(); pctx.stroke();
      pctx.globalAlpha = 1;
      pctx.fillStyle = data;
      for (var k = 0; k < 9; k++) {
        var pa = rot + k * Math.PI * 2 / 9 - Math.PI / 2;
        pctx.beginPath();
        pctx.arc(cx + Math.cos(pa) * R, cy + Math.sin(pa) * R, 4.2, 0, Math.PI * 2);
        pctx.fill();
      }
      pctx.fillStyle = ink;
      pctx.beginPath(); pctx.arc(cx, cy, 4.5, 0, Math.PI * 2); pctx.fill();
      if (!reduced) requestAnimationFrame(drawPattern);
    }
    requestAnimationFrame(function (t) { t0 = t; drawPattern(t); });
  }

  /* Cohesion lift bars. Bar length is lift at window W = 20, from the
     AUDIT-091-V2 report. The dashed line at 1.0 is the shuffle null. */
  var lifts = [
    { label: "raw", value: 2.11, note: "Quran, surface forms" },
    { label: "Kalila stem", value: 1.82, note: "OpenITI prose control" },
    { label: "rasm", value: 1.68, note: "Quran, consonantal skeleton" },
    { label: "stem", value: 1.65, note: "Quran, light stem" },
    { label: "root", value: 1.49, note: "Quran, triliteral root" }
  ];
  var liftEl = document.querySelector("[data-lift]");
  if (liftEl) {
    var max = 2.4, W = 760, rowH = 46, padL = 118, padR = 52, top = 26;
    var H = top + lifts.length * rowH + 24;
    var scaleW = W - padL - padR;
    var s = '<svg viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="Bar chart of cohesion lift at window 20. Raw 2.11, Kalila stem 1.82, rasm 1.68, stem 1.65, root 1.49. The shuffle null sits at 1.0.">';
    var nullX = padL + scaleW * (1 / max);
    s += '<line x1="' + nullX + '" y1="' + (top - 8) + '" x2="' + nullX + '" y2="' + (H - 18) + '" stroke="currentColor" stroke-dasharray="4 4" opacity="0.55"/>';
    s += '<text x="' + nullX + '" y="' + (top - 12) + '" text-anchor="middle" font-size="11" fill="currentColor" opacity="0.7">null 1.0</text>';
    lifts.forEach(function (d, i) {
      var y = top + i * rowH;
      var bw = scaleW * (d.value / max);
      var fill = i === 1 ? "var(--data)" : "var(--accent)";
      s += '<text x="' + (padL - 10) + '" y="' + (y + 17) + '" text-anchor="end" font-size="13" fill="currentColor">' + d.label + '</text>';
      s += '<rect x="' + padL + '" y="' + y + '" width="' + bw.toFixed(1) + '" height="20" fill="' + fill + '" opacity="0.9"><title>' + d.label + ": lift " + d.value.toFixed(2) + " (" + d.note + ")</title></rect>";
      s += '<text x="' + (padL + bw + 8) + '" y="' + (y + 15) + '" font-size="13" fill="currentColor">' + d.value.toFixed(2) + "x</text>";
    });
    s += "</svg>";
    liftEl.innerHTML = s;
    liftEl.style.color = "var(--ink-2)";
  }

  /* Lineage spans. Bar position is the lifespan in the polymath report
     table (c. 780 to 1274 CE). End markers show the full veins range,
     c. 287 BCE to 1543 CE, stated in AUDIT-095R. */
  var scholars = [
    ["al-Khwarizmi", 780, 850], ["al-Kindi", 801, 873], ["Banu Musa", 803, 873],
    ["Thabit ibn Qurra", 836, 901], ["al-Karaji", 953, 1029], ["Ibn al-Haytham", 965, 1040],
    ["al-Biruni", 973, 1048], ["Ibn Sina", 980, 1037], ["al-Khayyam", 1048, 1131],
    ["Ibn Rushd", 1126, 1198], ["al-Samaw'al", 1130, 1180], ["al-Jazari", 1136, 1206],
    ["al-Tusi", 1201, 1274]
  ];
  var tl = document.querySelector("[data-timeline]");
  if (tl) {
    var x0 = -300, x1 = 1600, TW = 860, tPadL = 150, tPadR = 16, tTop = 30, tRow = 30;
    var TH = tTop + scholars.length * tRow + 40;
    function tx(year) { return tPadL + (year - x0) / (x1 - x0) * (TW - tPadL - tPadR); }
    var out = '<svg viewBox="0 0 ' + TW + ' ' + TH + '" role="img" aria-label="Lifespan bars for the thirteen scholars in the polymath lineage table, from about 780 to 1274 CE, inside the wider veins range of about 287 BCE to 1543 CE.">';
    [ -287, 0, 500, 780, 1000, 1274, 1543 ].forEach(function (yr) {
      var X = tx(yr);
      out += '<line x1="' + X.toFixed(1) + '" y1="' + (tTop - 6) + '" x2="' + X.toFixed(1) + '" y2="' + (TH - 26) + '" stroke="currentColor" opacity="0.14"/>';
      var lab = yr < 0 ? Math.abs(yr) + " BCE" : yr + "";
      out += '<text x="' + X.toFixed(1) + '" y="' + (tTop - 12) + '" text-anchor="middle" font-size="10" fill="currentColor" opacity="0.65">' + lab + "</text>";
    });
    scholars.forEach(function (sc, i) {
      var y = tTop + i * tRow;
      out += '<text x="' + (tPadL - 10) + '" y="' + (y + 13) + '" text-anchor="end" font-size="12" fill="currentColor">' + sc[0] + "</text>";
      out += '<rect x="' + tx(sc[1]).toFixed(1) + '" y="' + y + '" width="' + Math.max(3, tx(sc[2]) - tx(sc[1])).toFixed(1) + '" height="10" fill="var(--accent)" opacity="0.85"><title>' + sc[0] + ", c. " + sc[1] + " to " + sc[2] + " CE</title></rect>";
    });
    out += '<text x="' + tPadL + '" y="' + (TH - 8) + '" font-size="11" fill="currentColor" opacity="0.65">Full veins range: c. 287 BCE to 1543 CE (23 scholars). Bars show the 13 in the polymath table.</text>';
    out += "</svg>";
    tl.innerHTML = out;
    tl.style.color = "var(--ink-2)";
  }
})();
