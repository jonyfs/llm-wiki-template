/* Page behaviour: theme, nav menu, search, copy/share, metrics, reveal, service worker. */
(function () {
  'use strict';
  var d = document, root = d.documentElement;
  var $ = function (id) { return d.getElementById(id); };
  var T = function (k, v) { return window.llmwT ? window.llmwT(k, v) : k; };
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };

  /* Theme */
  var toggle = $('themeToggle');
  function setTheme(t, persist) {
    root.setAttribute('data-theme', t);
    if (persist) store.set('theme', t);
    var m = d.querySelector('meta[name="theme-color"]:not([media])');
    if (m) m.setAttribute('content', t === 'light' ? '#4f5bd5' : '#0b0d12');
  }
  if (toggle) toggle.addEventListener('click', function () {
    var next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    if (d.startViewTransition && !matchMedia('(prefers-reduced-motion: reduce)').matches) d.startViewTransition(function () { setTheme(next, true); });
    else setTheme(next, true);
  });
  var mq = matchMedia('(prefers-color-scheme: light)');
  var onScheme = function () { if (!store.get('theme')) setTheme(mq.matches ? 'light' : 'dark', false); };
  if (mq.addEventListener) mq.addEventListener('change', onScheme);

  /* Mobile menu */
  var btn = $('menuBtn'), panel = $('navPanel');
  function setMenu(open) {
    if (!btn || !panel) return;
    btn.setAttribute('aria-expanded', String(open));
    if (open) panel.setAttribute('data-open', ''); else panel.removeAttribute('data-open');
  }
  if (btn && panel) {
    btn.addEventListener('click', function () { setMenu(btn.getAttribute('aria-expanded') !== 'true'); });
    panel.addEventListener('click', function (e) { if (e.target.closest && e.target.closest('.nav-links a')) setMenu(false); });
    d.addEventListener('keydown', function (e) { if (e.key === 'Escape' && btn.getAttribute('aria-expanded') === 'true') { setMenu(false); btn.focus(); } });
    d.addEventListener('click', function (e) { if (btn.getAttribute('aria-expanded') === 'true' && !e.target.closest('.site-nav')) setMenu(false); });
    matchMedia('(min-width: 1300px)').addEventListener('change', function (e) { if (e.matches) setMenu(false); });
  }

  /* Progress bar + back to top (one rAF-throttled scroll handler) */
  var progress = $('progress'), top = $('backToTop'), ticking = false;
  function onScroll() {
    ticking = false;
    var max = (root.scrollHeight - root.clientHeight) || 1, y = root.scrollTop;
    if (progress) progress.style.transform = 'scaleX(' + Math.min(1, y / max) + ')';
    if (top) top.hidden = y < 600;
  }
  addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
  onScroll();
  if (top) top.addEventListener('click', function () { scrollTo({ top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }); });

  /* Scroll-spy for nav links */
  var links = [].slice.call(d.querySelectorAll('.nav-links a[href^="#"]'));
  if ('IntersectionObserver' in window && links.length) {
    var spy = new IntersectionObserver(function (en) {
      en.forEach(function (e) {
        if (!e.isIntersecting) return;
        links.forEach(function (a) { if (a.getAttribute('href') === '#' + e.target.id) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current'); });
      });
    }, { rootMargin: '-40% 0px -55% 0px' });
    links.forEach(function (a) { var s = d.querySelector(a.getAttribute('href')); if (s) spy.observe(s); });
  }

  /* Reveal on scroll (only when the head script added html.js) */
  if ('IntersectionObserver' in window && root.classList.contains('js')) {
    var io = new IntersectionObserver(function (en) { en.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }); }, { rootMargin: '0px 0px -5% 0px' });
    d.querySelectorAll('.card, .flow-card').forEach(function (el) { el.classList.add('reveal'); io.observe(el); });
  }

  /* Search: hides non-matching sections, says so when nothing matches */
  var search = $('siteSearch'), empty = $('searchEmpty'), secs = [].slice.call(d.querySelectorAll('main > section'));
  var texts = null;
  if (search) search.addEventListener('input', function () {
    if (!texts) texts = secs.map(function (s) { return s.textContent.toLowerCase(); });
    var q = search.value.trim().toLowerCase(), shown = 0;
    secs.forEach(function (s, i) { var ok = !q || texts[i].indexOf(q) !== -1; s.hidden = !ok; if (ok) shown++; });
    if (empty) { empty.hidden = !(q && !shown); empty.textContent = q && !shown ? T('app.nomatch', { q: search.value.trim() }) : ''; }
  });
  d.addEventListener('llmw:lang', function () { if (search && search.value) search.dispatchEvent(new Event('input')); });

  /* Copy quick start */
  var copy = $('copyQs'), qs = $('quickStart');
  function flash(el, key, back) { el.textContent = T(key); setTimeout(function () { el.textContent = T(back); }, 1400); }
  if (copy && qs) copy.addEventListener('click', function () {
    var p = navigator.clipboard ? navigator.clipboard.writeText(qs.innerText) : Promise.reject();
    p.then(function () { flash(copy, 'app.copied', 'app.copy'); }, function () { flash(copy, 'app.failed', 'app.copy'); });
  });

  /* Share */
  var share = $('shareBtn');
  if (share) share.addEventListener('click', function () {
    var data = { title: 'LLM Wiki Template', text: 'A persistent, compounding markdown knowledge base maintained by an LLM assistant.', url: 'https://github.com/jonyfs/llm-wiki-template' };
    if (navigator.share) { navigator.share(data).catch(function () {}); return; }
    if (navigator.clipboard) navigator.clipboard.writeText(data.url).then(function () { flash(share, 'app.linkCopied', 'app.share'); }, function () {});
  });

  /* Repo metrics (cached 10 min so reloads do not burn the unauthenticated API quota) */
  function paintMetrics(r) {
    var map = { mStars: ['m.stars', { n: r.stargazers_count }], mForks: ['m.forks', { n: r.forks_count }], mIssues: ['m.issues', { n: r.open_issues_count }], mUpdated: ['m.updated', { d: (r.updated_at || '').slice(0, 10) }] };
    Object.keys(map).forEach(function (id) { var el = $(id); if (el) el.textContent = T(map[id][0], map[id][1]); });
    paintMetrics.last = r;
  }
  d.addEventListener('llmw:lang', function () { if (paintMetrics.last) paintMetrics(paintMetrics.last); });
  (function () {
    var c = store.get('repoMetrics'), parsed = null;
    try { parsed = c && JSON.parse(c); } catch (e) {}
    if (parsed && Date.now() - parsed.t < 600000) { paintMetrics(parsed.r); return; }
    fetch('https://api.github.com/repos/jonyfs/llm-wiki-template').then(function (res) { return res.ok ? res.json() : null; }).then(function (r) {
      if (!r) return;
      paintMetrics(r); store.set('repoMetrics', JSON.stringify({ t: Date.now(), r: { stargazers_count: r.stargazers_count, forks_count: r.forks_count, open_issues_count: r.open_issues_count, updated_at: r.updated_at } }));
    }).catch(function () {});
  })();

  /* Service worker + update prompt (not shown on the very first install) */
  if ('serviceWorker' in navigator) {
    var hadController = !!navigator.serviceWorker.controller;
    addEventListener('load', function () { navigator.serviceWorker.register('./sw.js').catch(function () {}); });
    navigator.serviceWorker.addEventListener('controllerchange', function () {
      if (!hadController) { hadController = true; return; }
      var n = d.createElement('button');
      n.type = 'button'; n.className = 'toast'; n.setAttribute('role', 'status'); n.textContent = T('app.update');
      n.addEventListener('click', function () { location.reload(); });
      d.body.appendChild(n);
    });
  }
})();
