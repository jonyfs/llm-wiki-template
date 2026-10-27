/* Live wiki graph: a brain made of wiki pages. Canvas 2D with real perspective, depth sorting,
   neuron-shaped nodes, and three wiki operations (add a page, ask the wiki, run lint) played out on it.
   Simulated data only; no network. World space is centred on the origin. */
(function () {
  'use strict';
  var canvas = document.getElementById('g');
  if (!canvas || !canvas.getContext) return;
  var ctx = canvas.getContext('2d');
  var T = function (k, v) { return window.llmwT ? window.llmwT(k, v) : k; };
  var $ = function (id) { return document.getElementById(id); };
  var clamp = function (v, a, b) { return Math.max(a, Math.min(b, v)); };
  var reducedMQ = matchMedia('(prefers-reduced-motion: reduce)'), reduced = reducedMQ.matches;
  var coarse = matchMedia('(pointer: coarse)').matches;

  /* ---------- Data: a brain-shaped vault ---------- */
  var seed = 20260601;
  function rnd() { seed = (seed + 0x6D2B79F5) | 0; var t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }

  // Overlapping ellipsoids. side: -1 left hemisphere, 1 right, 0 on the midline.
  var LOBES = [
    { c: [-92, -18, 0], r: [150, 120, 130], w: 1.7, side: -1 },
    { c: [92, -18, 0], r: [150, 120, 130], w: 1.7, side: 1 },
    { c: [-125, 78, 14], r: [68, 52, 78], w: 0.7, side: -1 },
    { c: [125, 78, 14], r: [68, 52, 78], w: 0.7, side: 1 },
    { c: [0, -92, -6], r: [118, 66, 104], w: 0.9, side: 0 },
    { c: [0, 100, -92], r: [84, 54, 66], w: 0.8, side: 0 },
    { c: [0, 158, -40], r: [26, 62, 26], w: 0.35, side: 0 }
  ];
  var LOBE_SUM = LOBES.reduce(function (s, l) { return s + l.w; }, 0);
  var GAP = 7; // half-width of the longitudinal fissure between hemispheres
  var MAXN = 420;
  var POOL = {
    source: ['karpathy-gist', 'rag-survey', 'agent-notes', 'meeting-notes', 'attention-paper', 'podcast-transcript', 'eval-dataset', 'release-changelog', 'blog-post', 'api-reference', 'interview', 'whitepaper', 'lecture-slides', 'issue-thread'],
    entity: ['karpathy', 'obsidian', 'claude', 'openai', 'git', 'markdown', 'mcp', 'cursor', 'codex', 'copilot', 'github', 'vector-db'],
    concept: ['llm-wiki', 'compounding', 'ingest', 'query', 'lint', 'refresh', 'frontmatter', 'wikilink', 'citation', 'claims-ledger', 'index', 'log', 'schema', 'skills', 'retrieval', 'embeddings', 'contradiction', 'provenance'],
    synthesis: ['rag-vs-wiki', 'compounding-notes', 'agent-fit', 'ingest-playbook', 'citation-style', 'lint-findings', 'reading-list']
  };
  var DIR = { source: 'sources', entity: 'entities', concept: 'concepts', synthesis: 'syntheses' };
  var TYPES = ['source', 'entity', 'concept', 'synthesis'];
  // One neuron shape per page type, so the type reads without colour: [count, near, far, branch chance, apical length]
  var MORPH = { source: [3, 1.5, 2.8, 0.4, 6.2], entity: [8, 1.4, 2.6, 0.25, 0], concept: [5, 1.8, 3.6, 0.65, 0], synthesis: [6, 2.2, 5.2, 0.9, 0] };
  var used = {};
  function makeLabel(type, r) {
    var pool = POOL[type], base = pool[Math.floor(r() * pool.length)], key = type + '/' + base;
    used[key] = (used[key] || 0) + 1;
    return 'wiki/' + DIR[type] + '/' + base + (used[key] > 1 ? '-' + used[key] : '');
  }
  function pickType(r) { var x = r(); return x < 0.3 ? 'source' : x < 0.54 ? 'entity' : x < 0.86 ? 'concept' : 'synthesis'; }
  function pickLobe(r) { var x = r() * LOBE_SUM; for (var i = 0; i < LOBES.length; i++) { x -= LOBES[i].w; if (x <= 0) return i; } return LOBES.length - 1; }
  // Gyri and sulci: the outline of each lobe wobbles a little, so the shell reads as folded cortex.
  function fold(x, y, z) { return 1 + 0.05 * (Math.sin(x * 0.09) + Math.sin(y * 0.11 + 1.3) + Math.sin(z * 0.1 + 2.1)); }
  function pointIn(l, r) {
    var u = r() * 6.2832, v = r() * 2 - 1, s = Math.sqrt(1 - v * v), L = LOBES[l];
    var k = r() < 0.72 ? 0.9 + r() * 0.1 : 0.35 + Math.cbrt(r()) * 0.5; // most pages sit in the cortex, the rest in white matter
    return [L.c[0] + L.r[0] * s * Math.cos(u) * k, L.c[1] + L.r[1] * s * Math.sin(u) * k, L.c[2] + L.r[2] * v * k];
  }

  var nodes = [], edges = [], edgeSet = {}, edgeIdx = {}, order = [];
  function addEdge(a, b, tract) {
    if (a === b) return false;
    var k = a < b ? a + ',' + b : b + ',' + a;
    if (edgeSet[k]) return false;
    edgeSet[k] = 1; edgeIdx[k] = edges.length;
    edges.push([a, b, (rnd() < 0.5 ? -1 : 1) * (0.04 + rnd() * 0.08), !!tract]);
    nodes[a].deg++; nodes[b].deg++; nodes[a].adj.push(b); nodes[b].adj.push(a);
    return true;
  }
  function findEdge(a, b) { var k = a < b ? a + ',' + b : b + ',' + a; return edgeIdx[k]; }
  // Dendrites are stored in soma radii: they scale with the cell and rotate with the camera.
  function makeDendrites(type, r) {
    var m = MORPH[type], out = [], i, count = m[0] + Math.floor(r() * 2);
    function jit() { return (r() - 0.5) * 0.9; }
    function dir() { var u = r() * 6.2832, v = r() * 2 - 1, s = Math.sqrt(1 - v * v); return [s * Math.cos(u), v, s * Math.sin(u)]; }
    for (i = 0; i < count; i++) {
      var d = dir(), a = m[1] + r() * 0.7, b = m[2] + r() * 1.6;
      var den = { m: [d[0] * a + jit(), d[1] * a + jit(), d[2] * a + jit()], t: [d[0] * b + jit(), d[1] * b + jit(), d[2] * b + jit()], b: null };
      if (r() < m[3]) { var q = dir(), l = 1.2 + r() * 1.2; den.b = [den.m[0] + q[0] * l, den.m[1] + q[1] * l, den.m[2] + q[2] * l]; }
      out.push(den);
    }
    if (m[4]) out.push({ m: [0.2, -m[4] * 0.55, 0], t: [0, -m[4], 0.2], b: [0.9, -m[4] * 0.8, 0.3] }); // the pyramidal cell's long apical dendrite
    return out;
  }
  function addNode(type, r, near) {
    var lobe = near != null ? nodes[near].lobe : pickLobe(r), p = pointIn(lobe, r);
    if (near != null) { var q = nodes[near]; p = [q.x + (r() - 0.5) * 30, q.y + (r() - 0.5) * 30, q.z + (r() - 0.5) * 30]; }
    var n = { id: nodes.length, type: type, label: makeLabel(type, r), lobe: lobe, side: LOBES[lobe].side, x: p[0], y: p[1], z: p[2], vx: 0, vy: 0, vz: 0, deg: 0, adj: [], pulse: 0, lit: 0, px: 0, py: 0, pz: 0, pr: 0, pd: 0, pp: 1, den: makeDendrites(type, r) };
    nodes.push(n); order.push(n);
    return n;
  }
  // Preferential attachment, biased to the same lobe: hubs and communities like a real vault.
  // About one link in eight crosses the midline, like the corpus callosum.
  function link(n, count, r) {
    for (var c = 0; c < count; c++) {
      var total = 0, w = [], i, cross = n.side !== 0 && r() < 0.13;
      for (i = 0; i < n.id; i++) {
        var o = nodes[i], dx = o.x - n.x, dy = o.y - n.y, dz = o.z - n.z, x;
        if (cross) x = o.side === -n.side ? (o.deg + 1.2) * Math.exp(-(Math.abs(dy) + Math.abs(dz)) / 60) : 0;
        else x = (o.deg + 1.2) * Math.exp(-Math.sqrt(dx * dx + dy * dy + dz * dz) / 55);
        x += 1e-6; w.push(x); total += x;
      }
      var t = r() * total;
      for (i = 0; i < w.length; i++) { t -= w[i]; if (t <= 0) break; }
      var j = Math.min(i, n.id - 1);
      addEdge(n.id, j, nodes[j].side === -n.side && n.side !== 0);
    }
  }
  for (var gi = 0; gi < 230; gi++) {
    var nn = addNode(pickType(rnd), rnd);
    if (nn.id > 0) { var x0 = rnd(); link(nn, 1 + (x0 < 0.55 ? 1 : 0) + (x0 < 0.2 ? 1 : 0), rnd); }
  }

  /* ---------- Physics ---------- */
  var alpha = 1, REPEL = 1100, CUT2 = 150 * 150, REST = 34;
  function simStep(k) {
    var n = nodes.length, a, b, dx, dy, dz, d2, d, f, i, j;
    for (i = 0; i < n; i++) {
      a = nodes[i];
      for (j = i + 1; j < n; j++) {
        b = nodes[j]; dx = b.x - a.x; dy = b.y - a.y; dz = b.z - a.z; d2 = dx * dx + dy * dy + dz * dz + 1;
        if (d2 > CUT2) continue;
        d = Math.sqrt(d2); f = (REPEL * k) / d2 / d;
        a.vx -= f * dx; a.vy -= f * dy; a.vz -= f * dz; b.vx += f * dx; b.vy += f * dy; b.vz += f * dz;
      }
    }
    for (i = 0; i < edges.length; i++) {
      a = nodes[edges[i][0]]; b = nodes[edges[i][1]]; dx = b.x - a.x; dy = b.y - a.y; dz = b.z - a.z;
      d = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1; f = ((d - REST) * 0.018 * k) / d;
      a.vx += f * dx; a.vy += f * dy; a.vz += f * dz; b.vx -= f * dx; b.vy -= f * dy; b.vz -= f * dz;
    }
    for (i = 0; i < n; i++) {
      a = nodes[i]; var L = LOBES[a.lobe];
      var ex = (a.x - L.c[0]) / L.r[0], ey = (a.y - L.c[1]) / L.r[1], ez = (a.z - L.c[2]) / L.r[2], q = Math.sqrt(ex * ex + ey * ey + ez * ez), lim = 0.97 * fold(a.x, a.y, a.z);
      if (q > lim) { var pull = (q - lim) * 0.12; a.vx += (L.c[0] - a.x) * pull; a.vy += (L.c[1] - a.y) * pull; a.vz += (L.c[2] - a.z) * pull; }
      a.vx *= 0.84; a.vy *= 0.84; a.vz *= 0.84; a.x += a.vx; a.y += a.vy; a.z += a.vz;
      if (a.side && a.x * a.side < GAP) a.x = a.side * GAP; // keep the hemispheres apart
    }
  }
  var t0 = performance.now();
  for (var s = 0, steps = reduced ? 260 : 110; s < steps; s++) { simStep(alpha); alpha *= reduced ? 0.985 : 0.965; } // reduced motion settles fully up front; otherwise the rest plays out on screen
  var settleMs = Math.round(performance.now() - t0);
  alpha = reduced ? 0 : 0.5;

  /* ---------- Theme ---------- */
  var COLORS = {
    dark: { source: '#5eead4', entity: '#fbbf24', concept: '#8b97ff', synthesis: '#f472b6' },
    light: { source: '#0f766e', entity: '#b45309', concept: '#4338ca', synthesis: '#be185d' }
  };
  var pal, palRGB = {}, edgeRGB = '139,151,255', labelColor = '#e8eaf0', bgColor = '#0d1017', warnColor = '#f59e0b', sprites = {}, ghost = null, ghostAlpha = 0.5;
  function hexToRgb(h) { return [parseInt(h.substr(1, 2), 16), parseInt(h.substr(3, 2), 16), parseInt(h.substr(5, 2), 16)]; }
  function mix(h, t, amt) { var c = hexToRgb(h); return 'rgb(' + c.map(function (v, i) { return Math.round(v + (t[i] - v) * amt); }).join(',') + ')'; }
  function makeSprite(color, glow) {
    var S = 96, c = document.createElement('canvas'); c.width = c.height = S; var g = c.getContext('2d');
    var rgb = hexToRgb(color), gl = g.createRadialGradient(S / 2, S / 2, S * 0.08, S / 2, S / 2, S / 2);
    gl.addColorStop(0, 'rgba(' + rgb + ',' + glow + ')'); gl.addColorStop(1, 'rgba(' + rgb + ',0)');
    g.fillStyle = gl; g.fillRect(0, 0, S, S);
    var b = g.createRadialGradient(S / 2 - S * 0.07, S / 2 - S * 0.08, S * 0.015, S / 2, S / 2, S * 0.22);
    b.addColorStop(0, mix(color, [255, 255, 255], 0.6)); b.addColorStop(0.55, color); b.addColorStop(1, mix(color, [0, 0, 0], 0.4));
    g.fillStyle = b; g.beginPath(); g.arc(S / 2, S / 2, S * 0.22, 0, 6.2832); g.fill();
    return c;
  }
  function makeGhost(rgb) { // a soft blob that outlines each lobe, so the brain shape stays readable behind the cells
    var S = 128, c = document.createElement('canvas'); c.width = c.height = S; var g = c.getContext('2d'), gr = g.createRadialGradient(S / 2, S / 2, S * 0.12, S / 2, S / 2, S / 2);
    gr.addColorStop(0, 'rgba(' + rgb + ',0.2)'); gr.addColorStop(0.75, 'rgba(' + rgb + ',0.1)'); gr.addColorStop(1, 'rgba(' + rgb + ',0)');
    g.fillStyle = gr; g.fillRect(0, 0, S, S);
    return c;
  }
  function readTheme() {
    var light = document.documentElement.getAttribute('data-theme') === 'light', cs = getComputedStyle(canvas.parentNode);
    pal = COLORS[light ? 'light' : 'dark'];
    edgeRGB = (cs.getPropertyValue('--g-edge') || '139 151 255').trim().replace(/\s+/g, ',');
    labelColor = (cs.getPropertyValue('--g-label') || '#e8eaf0').trim();
    bgColor = (cs.getPropertyValue('--g-bg') || '#0d1017').trim();
    warnColor = light ? '#b45309' : '#f59e0b'; ghostAlpha = light ? 0.7 : 0.55;
    TYPES.forEach(function (t) { sprites[t] = makeSprite(pal[t], light ? 0.22 : 0.4); palRGB[t] = hexToRgb(pal[t]).join(','); });
    ghost = makeGhost(edgeRGB);
    document.querySelectorAll('.type[data-type]').forEach(function (b) { b.style.setProperty('--c', pal[b.getAttribute('data-type')]); });
    dirty = true;
  }

  /* ---------- Camera ---------- */
  var W = 1, H = 1, dpr = 1, cssW = 1, cssH = 1, yaw = 0.6, pitch = -0.22, zoom = 1, panX = 0, panY = 0, vyaw = 0, vpitch = 0, DIST = 820;
  var tz = 1, tpx = 0, tpy = 0, animating = false; // eased targets for buttons, wheel and fly-to
  var hidden = {}, hovered = -1, selected = -1, auto = !reduced, orbit = false, dirty = true, visible = true, dragging = false, raf = 0, last = 0, tNow = 0;
  var camCy = 1, camSy = 0, camCp = 1, camSp = 0, S0 = 1, CX = 0, CY = 0, R1 = { x: 0, y: 0 }, R2 = { x: 0, y: 0 }, R3 = { x: 0, y: 0 };
  function rotv(v, o) { var x1 = v[0] * camCy + v[2] * camSy, z1 = -v[0] * camSy + v[2] * camCy; o.x = x1; o.y = v[1] * camCp - z1 * camSp; }
  function ctrl(a, b, k) { CX = (a.px + b.px) / 2 - (b.py - a.py) * k; CY = (a.py + b.py) / 2 + (b.px - a.px) * k; }
  function project() {
    var cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
    var breathe = reduced || quality === 0 ? 1 : 1 + 0.008 * Math.sin(tNow / 1700);
    S0 = (Math.min(W, H * 1.05) / 470) * zoom * breathe;
    camCy = cy; camSy = sy; camCp = cp; camSp = sp;
    var cx = W / 2 + panX, cyy = H / 2 + panY, rk = S0 * Math.pow(zoom, -0.35) * 0.62;
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i], x1 = n.x * cy + n.z * sy, z1 = -n.x * sy + n.z * cy, y1 = n.y * cp - z1 * sp, z2 = n.y * sp + z1 * cp, p = DIST / (DIST + z2);
      n.px = cx + x1 * p * S0; n.py = cyy + y1 * p * S0; n.pz = z2; n.pp = p; n.pd = clamp((z2 + 260) / 520, 0, 1);
      n.pr = (2.1 + Math.sqrt(n.deg) * 1.2 + n.pulse * 6) * p * rk;
    }
  }
  function focusId() { return hovered !== -1 ? hovered : selected; }

  /* ---------- Quality: lower the detail when frames get slow ---------- */
  var quality = 2, ema = 4, slow = 0, fast = 0, frames = 0;
  function tune(ms) {
    ema = ema * 0.9 + ms * 0.1; frames++;
    if (frames % 20) return;
    if (ema > 13) { fast = 0; if (++slow >= 2 && quality > 0) { quality--; slow = 0; } }
    else if (ema < 5) { slow = 0; if (++fast >= 10 && quality < 2) { quality++; fast = 0; } }
    else { slow = 0; fast = 0; }
  }

  /* ---------- Draw ---------- */
  var tips = [], nb = new Uint8Array(MAXN + 8), widths = {}, bk = [[], [], [], []], strong = [], tracts = [];
  function drawGhost() {
    if (!ghost) return;
    ctx.globalAlpha = ghostAlpha;
    for (var i = 0; i < LOBES.length; i++) {
      var L = LOBES[i], x = L.c[0] * camCy + L.c[2] * camSy, z1 = -L.c[0] * camSy + L.c[2] * camCy, y = L.c[1] * camCp - z1 * camSp, z2 = L.c[1] * camSp + z1 * camCp, p = DIST / (DIST + z2);
      var rx = Math.max(L.r[0], L.r[2]) * 1.08 * p * S0, ry = L.r[1] * 1.12 * p * S0;
      ctx.drawImage(ghost, W / 2 + panX + x * p * S0 - rx, H / 2 + panY + y * p * S0 - ry, rx * 2, ry * 2);
    }
    ctx.globalAlpha = 1;
  }
  function drawDendrites(n, al) {
    var big = n.pr > 2.2 * dpr; if (quality === 0 || !big) return;
    var k = n.pr * Math.min(1, (40 * dpr) / (5 * n.pr)), col = palRGB[n.type], i, d, mx, my, tx, ty, nt = 0, bw = Math.max(0.9 * dpr, n.pr * 0.16);
    ctx.strokeStyle = 'rgba(' + col + ',' + al + ')'; ctx.lineWidth = Math.max(0.7 * dpr, n.pr * 0.1); ctx.lineCap = 'round';
    ctx.beginPath();
    for (i = 0; i < n.den.length; i++) {
      d = n.den[i]; rotv(d.m, R1); rotv(d.t, R2);
      mx = n.px + R1.x * k; my = n.py + R1.y * k; tx = n.px + R2.x * k; ty = n.py + R2.y * k;
      ctx.moveTo(n.px, n.py); ctx.quadraticCurveTo(mx + (ty - my) * 0.3, my - (tx - mx) * 0.3, tx, ty); tips[nt++] = tx; tips[nt++] = ty;
      if (d.b && quality > 1) { rotv(d.b, R3); ctx.moveTo(mx, my); ctx.lineTo(n.px + R3.x * k, n.py + R3.y * k); tips[nt++] = n.px + R3.x * k; tips[nt++] = n.py + R3.y * k; }
    }
    ctx.stroke();
    ctx.fillStyle = 'rgba(' + col + ',' + al + ')'; ctx.beginPath();
    for (i = 0; i < nt; i += 2) { ctx.moveTo(tips[i] + bw, tips[i + 1]); ctx.arc(tips[i], tips[i + 1], bw, 0, 6.2832); }
    ctx.fill();
  }
  // Action potentials: bright dots that travel along connections and sometimes continue to a neighbour.
  var signals = [];
  function sendSignal(from, to, gen) {
    var e = findEdge(from, to); if (e == null || signals.length > (quality > 1 ? 14 : 6)) return;
    signals.push({ e: e, t: 0, v: 0.008 + Math.random() * 0.01, rev: edges[e][1] === from, gen: gen || 0 });
  }
  function spawnSignal() {
    if (reduced || !edges.length) return;
    var e = Math.floor(Math.random() * edges.length), ed = edges[e];
    if (hidden[nodes[ed[0]].type] || hidden[nodes[ed[1]].type]) return;
    sendSignal(Math.random() < 0.5 ? ed[0] : ed[1], Math.random() < 0.5 ? ed[1] : ed[0], 0);
  }
  function drawSignals(fn, f) {
    for (var i = 0; i < signals.length; i++) {
      var s = signals[i], ed = edges[s.e], a = nodes[s.rev ? ed[1] : ed[0]], b = nodes[s.rev ? ed[0] : ed[1]], t = s.t, u = 1 - t;
      ctrl(a, b, s.rev ? -ed[2] : ed[2]);
      var x = u * u * a.px + 2 * u * t * CX + t * t * b.px, y = u * u * a.py + 2 * u * t * CY + t * t * b.py;
      var al = (1 - ((a.pd + b.pd) / 2) * 0.6) * (fn && ed[0] !== f && ed[1] !== f ? 0.3 : 1);
      if (quality > 0) { ctx.globalAlpha = clamp(al, 0.1, 1) * 0.35; ctx.fillStyle = 'rgb(' + palRGB[a.type] + ')'; ctx.beginPath(); ctx.arc(x, y, 5.5 * dpr, 0, 6.2832); ctx.fill(); }
      ctx.globalAlpha = clamp(al, 0.1, 1); ctx.fillStyle = labelColor; ctx.beginPath(); ctx.arc(x, y, 2 * dpr, 0, 6.2832); ctx.fill();
    }
    ctx.globalAlpha = 1;
  }
  function edgePath(list) {
    for (var i = 0; i < list.length; i++) { var ed = edges[list[i]], na = nodes[ed[0]], nb2 = nodes[ed[1]]; ctrl(na, nb2, ed[2]); ctx.moveTo(na.px, na.py); ctx.quadraticCurveTo(CX, CY, nb2.px, nb2.py); }
  }
  function offscreen(a, b) { var m = 60 * dpr; return (a.px < -m && b.px < -m) || (a.px > W + m && b.px > W + m) || (a.py < -m && b.py < -m) || (a.py > H + m && b.py > H + m); }
  function draw() {
    ctx.clearRect(0, 0, W, H);
    project();
    drawGhost();
    var f = focusId(), fn = f >= 0 ? nodes[f] : null, i, e, a, b, q;
    nb.fill(0, 0, nodes.length);
    if (fn) { nb[f] = 1; for (i = 0; i < fn.adj.length; i++) nb[fn.adj[i]] = 1; }
    // edges: four depth buckets (far = faint), then hub links and midline tracts on top
    for (q = 0; q < 4; q++) bk[q].length = 0; strong.length = 0; tracts.length = 0;
    for (i = 0; i < edges.length; i++) {
      e = edges[i]; a = nodes[e[0]]; b = nodes[e[1]];
      if (hidden[a.type] || hidden[b.type] || offscreen(a, b)) continue;
      if (e[3]) tracts.push(i); else if (Math.min(a.deg, b.deg) >= 4) strong.push(i);
      bk[quality ? Math.min(3, Math.floor(((a.pd + b.pd) / 2) * 4)) : 1].push(i);
    }
    ctx.lineWidth = Math.max(1, dpr * 0.9);
    for (q = 3; q >= 0; q--) {
      if (!bk[q].length) continue;
      var base = 0.34 - q * 0.075;
      ctx.strokeStyle = 'rgba(' + edgeRGB + ',' + (fn ? base * 0.3 : base) + ')'; ctx.beginPath(); edgePath(bk[q]); ctx.stroke();
    }
    if (strong.length) { ctx.lineWidth = dpr * 1.5; ctx.strokeStyle = 'rgba(' + edgeRGB + ',' + (fn ? 0.1 : 0.26) + ')'; ctx.beginPath(); edgePath(strong); ctx.stroke(); }
    if (tracts.length) { ctx.lineWidth = dpr * 1.7; ctx.strokeStyle = 'rgba(' + palRGB.entity + ',' + (fn ? 0.12 : 0.34) + ')'; ctx.beginPath(); edgePath(tracts); ctx.stroke(); }
    if (fn) {
      ctx.strokeStyle = 'rgba(' + edgeRGB + ',0.9)'; ctx.lineWidth = dpr * 1.7; ctx.beginPath();
      for (i = 0; i < edges.length; i++) { e = edges[i]; if (e[0] !== f && e[1] !== f) continue; a = nodes[e[0]]; b = nodes[e[1]]; if (hidden[a.type] || hidden[b.type]) continue; ctrl(a, b, e[2]); ctx.moveTo(a.px, a.py); ctx.quadraticCurveTo(CX, CY, b.px, b.py); }
      ctx.stroke();
    }
    // cells, far to near. The order array is almost sorted between frames, so an insertion sort is enough.
    for (i = 1; i < order.length; i++) { var cur = order[i], j = i - 1; while (j >= 0 && order[j].pz < cur.pz) { order[j + 1] = order[j]; j--; } order[j + 1] = cur; }
    var m = 70 * dpr, warn = tNow < flagUntil;
    for (i = 0; i < order.length; i++) {
      var n = order[i];
      if (hidden[n.type] || n.px < -m || n.px > W + m || n.py < -m || n.py > H + m) continue;
      var dim = fn && !nb[n.id], al = clamp((1 - n.pd * 0.62) * (dim ? 0.16 : 1), 0.05, 1), size = n.pr * 4.55;
      ctx.globalAlpha = 1; drawDendrites(n, al * 0.65);
      ctx.globalAlpha = al; ctx.drawImage(sprites[n.type], n.px - size / 2, n.py - size / 2, size, size);
      if (n.pulse > 0 && quality > 1) { ctx.globalAlpha = n.pulse * 0.5 * al; ctx.lineWidth = dpr; ctx.strokeStyle = 'rgb(' + palRGB[n.type] + ')'; ctx.beginPath(); ctx.arc(n.px, n.py, n.pr * (1.3 + (1 - n.pulse) * 2.4), 0, 6.2832); ctx.stroke(); }
      ctx.globalAlpha = 1;
      if (n.id === f || n.id === selected || tNow < n.lit) { ctx.lineWidth = dpr * 1.5; ctx.strokeStyle = labelColor; ctx.beginPath(); ctx.arc(n.px, n.py, n.pr * 1.45 + dpr * 2, 0, 6.2832); ctx.stroke(); }
      if (warn && n.flag) { ctx.lineWidth = dpr * 1.6; ctx.strokeStyle = warnColor; ctx.setLineDash([3 * dpr, 3 * dpr]); ctx.beginPath(); ctx.arc(n.px, n.py, n.pr * 1.9 + dpr * 3, 0, 6.2832); ctx.stroke(); ctx.setLineDash([]); }
    }
    drawSignals(fn, f);
    // labels: focus, neighbours and lit pages first, then the biggest hubs when there is room
    var cand = [];
    for (i = 0; i < nodes.length; i++) {
      n = nodes[i]; if (hidden[n.type]) continue;
      var pri = n.id === f ? 0 : fn && nb[n.id] ? 1 : tNow < n.lit ? 1.5 : !fn && n.deg >= 9 ? 2 + (20 - n.deg) / 100 : -1;
      if (pri >= 0) cand.push([pri, n]);
    }
    cand.sort(function (p, r) { return p[0] - r[0]; });
    ctx.font = '600 ' + Math.round(12 * dpr) + 'px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic'; ctx.lineJoin = 'round';
    var drawn = [];
    for (i = 0; i < cand.length && i < 40; i++) {
      n = cand[i][1];
      var t = n.label.replace(/^wiki\/[a-z]+\//, ''), w = widths[t] || (widths[t] = ctx.measureText(t).width), x = n.px, y = n.py - n.pr * 1.5 - 5 * dpr, hit = false;
      for (var k = 0; k < drawn.length; k++) { var rr = drawn[k]; if (Math.abs(rr[0] - x) < (rr[2] + w) / 2 + 4 && Math.abs(rr[1] - y) < 15 * dpr) { hit = true; break; } }
      if (hit && cand[i][0] > 0) continue;
      drawn.push([x, y, w]);
      ctx.globalAlpha = cand[i][0] === 0 ? 1 : 0.5 + 0.5 * (1 - n.pd);
      ctx.lineWidth = 4 * dpr; ctx.strokeStyle = bgColor; ctx.strokeText(t, x, y); ctx.fillStyle = labelColor; ctx.fillText(t, x, y);
    }
    ctx.globalAlpha = 1;
  }

  /* ---------- Wiki operations played on the brain ---------- */
  var info = $('gInfo'), statusEl = $('gStatus'), tip = $('gTip'), flagUntil = 0, waves = [], pendingAnswer = null, answers = 0;
  function say(key, vars) { if (statusEl) statusEl.textContent = T(key, vars); }
  function ingest(announce) {
    if (nodes.length >= MAXN) { if (announce) say('g.cap', { n: MAXN }); return; }
    var type = pickType(Math.random), near = Math.floor(Math.random() * nodes.length), n = addNode(type, Math.random, near);
    link(n, 2 + Math.floor(Math.random() * 3), Math.random); addEdge(near, n.id);
    n.pulse = 1; alpha = Math.max(alpha, 0.55); refreshStats();
    if (announce) say('g.added', { name: n.label });
    wake();
  }
  function ask() {
    if (waves.length || pendingAnswer || nodes.length >= MAXN) { if (nodes.length >= MAXN) say('g.cap', { n: MAXN }); return; }
    var pool = nodes.filter(function (n) { return (n.type === 'concept' || n.type === 'entity') && n.deg >= 3 && !hidden[n.type]; });
    if (!pool.length) return;
    var seedN = pool[Math.floor(Math.random() * pool.length)], seen = {}, queue = [[seedN.id, -1, 0]], hits = [], now = performance.now();
    seen[seedN.id] = 1;
    while (queue.length && hits.length < 14) { // breadth-first walk along wikilinks, two hops deep
      var cur = queue.shift(); hits.push(cur);
      if (cur[2] >= 2) continue;
      var nbs = nodes[cur[0]].adj.slice().sort(function (a, b) { return nodes[b].deg - nodes[a].deg; }).slice(0, 4);
      for (var i = 0; i < nbs.length; i++) if (!seen[nbs[i]]) { seen[nbs[i]] = 1; queue.push([nbs[i], cur[0], cur[2] + 1]); }
    }
    hits.forEach(function (h) { waves.push({ id: h[0], from: h[1], at: now + h[2] * 420 + Math.random() * 120 }); });
    pendingAnswer = { at: now + 2 * 420 + 900, ids: hits.map(function (h) { return h[0]; }) };
    selected = seedN.id; updateInfo(false); say('g.askStart', { name: seedN.label.replace(/^wiki\/[a-z]+\//, '') });
    wake();
  }
  function stepWaves() {
    var busy = false, i, w;
    for (i = waves.length - 1; i >= 0; i--) {
      w = waves[i]; busy = true;
      if (tNow < w.at) continue;
      nodes[w.id].pulse = 1; nodes[w.id].lit = tNow + 3200;
      if (w.from >= 0 && !reduced) sendSignal(w.from, w.id, 2);
      waves.splice(i, 1);
    }
    if (pendingAnswer && !waves.length && tNow >= pendingAnswer.at) {
      var ids = pendingAnswer.ids; pendingAnswer = null; answers++;
      var n = addNode('synthesis', Math.random, ids[0]); n.label = 'wiki/syntheses/answer-' + answers;
      ids.slice(0, 5).forEach(function (id) { addEdge(n.id, id); });
      n.pulse = 1; n.lit = tNow + 3200; alpha = Math.max(alpha, 0.5); refreshStats();
      say('g.asked', { n: ids.length, name: n.label.replace(/^wiki\/[a-z]+\//, '') });
    } else if (pendingAnswer) busy = true;
    return busy;
  }
  function lint() {
    var weak = 0; nodes.forEach(function (n) { n.flag = n.deg <= 1 && !hidden[n.type]; if (n.flag) weak++; });
    flagUntil = performance.now() + 4200; say(weak ? 'g.lint' : 'g.lintOk', { n: weak }); wake();
  }

  /* ---------- Loop ---------- */
  function request() { if (!raf && visible && !document.hidden) raf = requestAnimationFrame(frame); }
  function wake() { dirty = true; request(); }
  var hoverReq = null;
  function frame(t) {
    raf = 0; tNow = t;
    var dt = Math.min(48, t - (last || t)) / 16.67; last = t;
    var busy = false, t0f = performance.now(), i;
    if (hoverReq) { setHover(pick(hoverReq.x, hoverReq.y)); hoverReq = null; }
    if (alpha > 0.02) { simStep(alpha); alpha *= 0.965; busy = true; } else alpha = 0;
    if (!dragging) {
      if (Math.abs(vyaw) > 1e-4 || Math.abs(vpitch) > 1e-4) { yaw += vyaw * dt; pitch = clamp(pitch + vpitch * dt, -1.25, 1.25); vyaw *= 0.94; vpitch *= 0.94; busy = true; }
      else if (auto && hovered === -1 && !reduced) { yaw += 0.0024 * dt; busy = true; }
    }
    if (animating) { // ease toward the zoom/pan targets
      var k = 1 - Math.pow(0.001, dt / 14);
      zoom += (tz - zoom) * k; panX += (tpx - panX) * k; panY += (tpy - panY) * k;
      if (Math.abs(tz - zoom) < 0.002 && Math.abs(tpx - panX) < 0.4 && Math.abs(tpy - panY) < 0.4) { zoom = tz; panX = tpx; panY = tpy; animating = false; }
      busy = true;
    }
    if (!reduced && quality > 0) {
      if (Math.random() < 0.06 * dt) spawnSignal();
    }
    for (i = signals.length - 1; i >= 0; i--) {
      var sg = signals[i]; sg.t += sg.v * dt; busy = true;
      if (sg.t >= 1) {
        var ed = edges[sg.e], to = sg.rev ? ed[0] : ed[1], tn = nodes[to];
        tn.pulse = Math.max(tn.pulse, 0.5); signals.splice(i, 1);
        if (sg.gen < 2 && Math.random() < 0.55 && tn.adj.length > 1) { // the signal carries on to another neighbour
          var nx = tn.adj[Math.floor(Math.random() * tn.adj.length)]; if (nx !== (sg.rev ? ed[1] : ed[0])) sendSignal(to, nx, sg.gen + 1);
        }
      }
    }
    if (stepWaves()) busy = true;
    for (i = 0; i < nodes.length; i++) { var n = nodes[i]; if (n.pulse > 0) { n.pulse = Math.max(0, n.pulse - 0.012 * dt); busy = true; } if (tNow < n.lit) busy = true; }
    if (tNow < flagUntil) busy = true; else if (flagUntil) { flagUntil = 0; nodes.forEach(function (x) { x.flag = false; }); dirty = true; }
    if (busy || dirty) {
      dirty = false;
      try { draw(); } catch (err) { quality = 0; signals.length = 0; if (window.console) console.warn('graph draw failed', err); return; }
      tune(performance.now() - t0f);
    }
    if (busy) request(); else last = 0;
  }

  /* ---------- UI text ---------- */
  function refreshStats() {
    var s = $('gStats'); if (s) s.textContent = T('g.stats', { n: nodes.length, e: edges.length });
    var c = {}; nodes.forEach(function (n) { c[n.type] = (c[n.type] || 0) + 1; });
    document.querySelectorAll('.type[data-type] .n').forEach(function (el) { el.textContent = c[el.parentNode.getAttribute('data-type')] || 0; });
    buildList();
  }
  function updateTip() { if (tip) tip.textContent = T(coarse ? 'g.hintTouch' : 'g.hintMouse'); }
  function shortName(n) { return n.label.replace(/^wiki\/[a-z]+\//, ''); }
  function updateInfo(announce) {
    var f = focusId();
    if (!info) return;
    if (f < 0) { info.hidden = true; return; }
    var n = nodes[f], names = n.adj.slice(0, 5).map(function (k) { return shortName(nodes[k]); });
    info.hidden = false; info.innerHTML = '';
    var b = document.createElement('b'); b.textContent = n.label; info.appendChild(b);
    var m = document.createElement('span'); m.textContent = T('type.' + n.type) + ' · ' + T('g.links', { n: n.deg }); info.appendChild(m);
    if (names.length) { var l = document.createElement('span'); l.textContent = T('g.linked', { list: names.join(', ') + (n.deg > 5 ? '…' : '') }); info.appendChild(l); }
    if (announce && statusEl) statusEl.textContent = n.label + ', ' + T('type.' + n.type) + ', ' + T('g.links', { n: n.deg });
  }
  var hubs = [], hubPos = -1;
  function buildList() {
    var listEl = $('gList'); hubs = nodes.slice().sort(function (a, b) { return b.deg - a.deg; });
    if (!listEl) return;
    listEl.innerHTML = '';
    hubs.slice(0, 12).forEach(function (n) {
      var li = document.createElement('li'), btn = document.createElement('button');
      btn.type = 'button'; btn.className = 'ctl'; btn.textContent = n.label.replace(/^wiki\//, '');
      btn.addEventListener('click', function () { selected = n.id; updateInfo(true); flyTo(n); });
      li.appendChild(btn); listEl.appendChild(li);
    });
  }

  /* ---------- Picking & camera moves ---------- */
  function pick(cx, cy) {
    var r = canvas.getBoundingClientRect(), x = (cx - r.left) * (W / r.width), y = (cy - r.top) * (H / r.height), best = -1, bd = 1e9, pad = (coarse ? 22 : 12) * dpr;
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i]; if (hidden[n.type]) continue;
      var d = Math.hypot(n.px - x, n.py - y) - n.pr;
      if (d < pad && d < bd) { bd = d; best = i; }
    }
    return best;
  }
  function setHover(h) { if (h !== hovered) { hovered = h; updateInfo(false); canvas.style.cursor = h >= 0 ? 'pointer' : ''; wake(); } }
  function zoomAt(z1, sx, sy, soft) { // zoom keeping the screen point (sx, sy) in place; coordinates in canvas device pixels
    z1 = clamp(z1, 0.55, 4);
    var z0 = soft ? tz : zoom, p0x = soft ? tpx : panX, p0y = soft ? tpy : panY, ox = sx - W / 2, oy = sy - H / 2;
    var nx = ox - (ox - p0x) * z1 / z0, ny = oy - (oy - p0y) * z1 / z0;
    if (soft) { tz = z1; tpx = nx; tpy = ny; animating = true; } else { zoom = tz = z1; panX = tpx = nx; panY = tpy = ny; animating = false; }
    wake();
  }
  function setZoom(z) { zoomAt(z, W / 2, H / 2, true); }
  function flyTo(n) { // bring a cell to the middle of the view and zoom in on it
    var z1 = clamp(Math.max(zoom, 2), 0.55, 4), ox = n.px - W / 2 - panX;
    tz = z1; tpx = -ox * z1 / zoom; tpy = -(n.py - H / 2 - panY) * z1 / zoom; animating = true; wake();
  }
  function resetView() { yaw = 0.6; pitch = -0.22; vyaw = vpitch = 0; tz = 1; tpx = tpy = 0; animating = true; selected = -1; hovered = -1; updateInfo(false); wake(); }

  /* ---------- Pointer input ---------- */
  var pts = {}, nPts = 0, down = null, pinch = null, hist = [], lastTap = null, panning = false;
  canvas.addEventListener('pointerdown', function (e) {
    pts[e.pointerId] = { x: e.clientX, y: e.clientY }; nPts++;
    try { canvas.setPointerCapture(e.pointerId); } catch (_) {}
    if (nPts === 1) {
      down = { x: e.clientX, y: e.clientY, t: performance.now(), moved: false, pan: e.button === 1 || e.button === 2 || e.shiftKey };
      panning = down.pan; dragging = true; vyaw = vpitch = 0; hist.length = 0; canvas.classList.add('grabbing');
    }
    if (nPts === 2) { var k = Object.keys(pts), a = pts[k[0]], b = pts[k[1]]; pinch = { d: Math.hypot(a.x - b.x, a.y - b.y), z: zoom, mx: (a.x + b.x) / 2, my: (a.y + b.y) / 2 }; }
  });
  canvas.addEventListener('pointermove', function (e) {
    var p = pts[e.pointerId];
    if (!p) { if (e.pointerType === 'mouse') { hoverReq = { x: e.clientX, y: e.clientY }; request(); } return; }
    var dx = e.clientX - p.x, dy = e.clientY - p.y; p.x = e.clientX; p.y = e.clientY;
    var r = canvas.getBoundingClientRect();
    if (nPts === 2 && pinch) { // pinch zooms around the midpoint and two fingers also pan
      var k = Object.keys(pts), a = pts[k[0]], b = pts[k[1]], mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
      zoomAt(pinch.z * Math.hypot(a.x - b.x, a.y - b.y) / pinch.d, (mx - r.left) * (W / r.width), (my - r.top) * (H / r.height), false);
      panX += (mx - pinch.mx) * (W / r.width); panY += (my - pinch.my) * (H / r.height); tpx = panX; tpy = panY; pinch.mx = mx; pinch.my = my; wake(); return;
    }
    var slop = e.pointerType === 'mouse' ? 4 : 10;
    if (down && Math.hypot(e.clientX - down.x, e.clientY - down.y) > slop) down.moved = true;
    if (down && down.moved) {
      if (panning) { panX += dx * (W / r.width); panY += dy * (H / r.height); tpx = panX; tpy = panY; wake(); return; }
      var ry = (dx / r.width) * Math.PI * 1.1, rx = (e.pointerType === 'touch' && !orbit) ? 0 : (dy / r.height) * Math.PI * 0.9; // the same drag turns the brain the same amount at any canvas size
      yaw += ry; pitch = clamp(pitch + rx, -1.25, 1.25); hist.push([performance.now(), ry, rx]); if (hist.length > 6) hist.shift(); wake();
    }
  });
  function end(e) {
    if (!pts[e.pointerId]) return;
    delete pts[e.pointerId]; nPts = Math.max(0, nPts - 1); pinch = null;
    try { canvas.releasePointerCapture(e.pointerId); } catch (_) {}
    if (nPts === 0) {
      dragging = false; panning = false; canvas.classList.remove('grabbing');
      var now = performance.now();
      if (down && !down.moved && e.type === 'pointerup' && now - down.t < 500) {
        var h = pick(e.clientX, e.clientY), dbl = lastTap && now - lastTap.t < 320 && Math.hypot(e.clientX - lastTap.x, e.clientY - lastTap.y) < 24;
        if (dbl) { if (h >= 0) { selected = h; updateInfo(true); flyTo(nodes[h]); } else resetView(); lastTap = null; }
        else { selected = h === selected ? -1 : h; hovered = e.pointerType === 'mouse' ? h : -1; updateInfo(true); if (selected < 0 && statusEl) statusEl.textContent = ''; if (selected >= 0 && navigator.vibrate && e.pointerType === 'touch') navigator.vibrate(8); lastTap = { t: now, x: e.clientX, y: e.clientY }; }
      } else if (down && down.moved && !reduced && hist.length > 1) { // inertia from the last ~100 ms of real movement
        var span = hist[hist.length - 1][0] - hist[0][0] || 1, sy = 0, sx = 0, idx;
        if (now - hist[hist.length - 1][0] < 80) { for (idx = 1; idx < hist.length; idx++) { sy += hist[idx][1]; sx += hist[idx][2]; } vyaw = (sy / span) * 16.67; vpitch = (sx / span) * 16.67; }
      }
      down = null; wake();
    }
  }
  canvas.addEventListener('pointerup', end);
  canvas.addEventListener('pointercancel', end);
  canvas.addEventListener('lostpointercapture', end);
  canvas.addEventListener('pointerleave', function (e) { if (e.pointerType === 'mouse' && !dragging) { hoverReq = null; setHover(-1); } });
  canvas.addEventListener('contextmenu', function (e) { e.preventDefault(); });
  canvas.addEventListener('wheel', function (e) {
    if (!(e.ctrlKey || e.metaKey)) return; // a plain wheel keeps scrolling the page
    e.preventDefault(); var r = canvas.getBoundingClientRect();
    zoomAt(zoom * Math.exp(-e.deltaY * (e.deltaMode ? 0.05 : 0.006)), (e.clientX - r.left) * (W / r.width), (e.clientY - r.top) * (H / r.height), false);
  }, { passive: false });
  canvas.addEventListener('keydown', function (e) {
    var k = e.key, step = 0.12, ok = true, id;
    if (k === 'ArrowLeft') yaw -= step; else if (k === 'ArrowRight') yaw += step;
    else if (k === 'ArrowUp') pitch = clamp(pitch - step, -1.25, 1.25); else if (k === 'ArrowDown') pitch = clamp(pitch + step, -1.25, 1.25);
    else if (k === '+' || k === '=') setZoom(zoom * 1.2); else if (k === '-' || k === '_') setZoom(zoom / 1.2);
    else if (k === '0') resetView(); else if (k === 'f' || k === 'F') toggleFs(); else if (k === 'Escape') { selected = -1; updateInfo(false); }
    else if (k === ']' || k === '[' || k === 'n' || k === 'p') { // step through pages from the most connected down
      hubPos = (hubPos + (k === ']' || k === 'n' ? 1 : -1) + hubs.length) % hubs.length; id = hubs[hubPos].id; selected = id; updateInfo(true);
    } else if (k === 'Enter' && selected >= 0) flyTo(nodes[selected]);
    else ok = false;
    if (ok) { e.preventDefault(); wake(); }
  });

  /* ---------- Controls ---------- */
  function on(id, fn) { var el = $(id); if (el) el.addEventListener('click', fn); }
  on('gZoomIn', function () { setZoom(tz * 1.25); });
  on('gZoomOut', function () { setZoom(tz / 1.25); });
  on('gZoomReset', resetView);
  on('gAdd', function () { ingest(true); });
  on('gAsk', ask);
  on('gLint', lint);
  var rotBtn = $('gRotate'), orbitBtn = $('gOrbit');
  function setOrbit(v, quiet) { orbit = v; canvas.style.touchAction = v ? 'none' : ''; if (orbitBtn) orbitBtn.setAttribute('aria-pressed', String(v)); if (!quiet) say(v ? 'g.orbitOn' : 'g.orbitOff'); }
  if (rotBtn) { rotBtn.setAttribute('aria-pressed', String(auto)); rotBtn.addEventListener('click', function () { auto = !auto; rotBtn.setAttribute('aria-pressed', String(auto)); wake(); }); }
  if (orbitBtn) orbitBtn.addEventListener('click', function () { setOrbit(!orbit); });
  document.querySelectorAll('.type[data-type]').forEach(function (b) {
    b.addEventListener('click', function () { var t = b.getAttribute('data-type'); hidden[t] = !hidden[t]; b.setAttribute('aria-pressed', String(!hidden[t])); wake(); });
  });
  // Full screen: the real Fullscreen API where it exists, a fixed-position fallback where it does not (iPhone Safari).
  var wrap = $('graphWrap'), fsBtn = $('gFull'), pseudoFs = false, fsOn = false, orbitBefore = false;
  function nativeFs() { return document.fullscreenElement || document.webkitFullscreenElement; }
  function syncFs() {
    var on = !!nativeFs() || pseudoFs;
    if (on === fsOn) return;
    fsOn = on;
    if (wrap) wrap.classList.toggle('is-full', on);
    document.documentElement.classList.toggle('graph-full', on);
    if (on) { orbitBefore = orbit; if (!orbit) setOrbit(true, true); } else if (!orbitBefore) setOrbit(false, true); // nothing to scroll in full screen, so touch can drag both ways
    labelFs(); say(on ? 'g.fsOn' : 'g.fsOff'); hoverReq = null; wake();
  }
  function labelFs() {
    if (!fsBtn) return;
    var txt = T(fsOn ? 'g.fsLabelOff' : 'g.fsLabelOn'); fsBtn.setAttribute('aria-pressed', String(fsOn)); fsBtn.setAttribute('aria-label', txt); fsBtn.setAttribute('title', txt);
  }
  function enterFs() {
    if (!wrap) return;
    var req = wrap.requestFullscreen || wrap.webkitRequestFullscreen;
    function fallback() { pseudoFs = true; syncFs(); }
    if (!req) { fallback(); return; }
    try { var p = req.call(wrap); if (p && p.catch) p.catch(fallback); } catch (_) { fallback(); }
  }
  function exitFs() {
    if (nativeFs()) { try { (document.exitFullscreen || document.webkitExitFullscreen).call(document); } catch (_) {} }
    if (pseudoFs) { pseudoFs = false; syncFs(); }
  }
  function toggleFs() { if (fsOn) exitFs(); else enterFs(); }
  on('gFull', toggleFs);
  document.addEventListener('fullscreenchange', syncFs);
  document.addEventListener('webkitfullscreenchange', syncFs);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && pseudoFs) { e.preventDefault(); exitFs(); } });
  // Scripted growth: one new page a minute for five minutes, only while the graph is on screen.
  var growTimer = 0, growUntil = Date.now() + 300000;
  if (!reduced) growTimer = setInterval(function () { if (Date.now() > growUntil) { clearInterval(growTimer); return; } if (visible && !document.hidden) ingest(false); }, 60000);

  /* ---------- Lifecycle ---------- */
  function resize() {
    var r = canvas.getBoundingClientRect(); cssW = Math.max(1, r.width); cssH = Math.max(1, r.height);
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    if (cssW * cssH * dpr * dpr > 2.6e6) dpr = Math.max(1, Math.sqrt(2.6e6 / (cssW * cssH))); // keep very large canvases affordable
    var w = Math.round(cssW * dpr), h = Math.round(cssH * dpr);
    if (w !== canvas.width || h !== canvas.height) { canvas.width = w; canvas.height = h; widths = {}; }
    W = canvas.width; H = canvas.height; wake();
  }
  if ('ResizeObserver' in window) new ResizeObserver(resize).observe(canvas); else window.addEventListener('resize', resize);
  if ('IntersectionObserver' in window) new IntersectionObserver(function (en) { visible = en[0].isIntersecting; if (visible) wake(); }, { threshold: 0 }).observe(canvas);
  document.addEventListener('visibilitychange', function () { if (!document.hidden) wake(); });
  window.addEventListener('blur', function () { dragging = false; panning = false; });
  new MutationObserver(function () { readTheme(); wake(); }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  if (reducedMQ.addEventListener) reducedMQ.addEventListener('change', function (e) { reduced = e.matches; if (reduced) { auto = false; signals.length = 0; if (rotBtn) rotBtn.setAttribute('aria-pressed', 'false'); } wake(); });
  document.addEventListener('llmw:lang', function () { refreshStats(); updateTip(); updateInfo(false); labelFs(); });

  window.llmwGraph = { stats: function () { return { nodes: nodes.length, edges: edges.length, quality: quality, frameMs: Math.round(ema * 10) / 10, settleMs: settleMs, signals: signals.length }; } };
  readTheme(); refreshStats(); updateTip(); resize();
})();
