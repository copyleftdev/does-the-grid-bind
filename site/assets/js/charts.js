/* Kinetic visualizations. Every chart draws itself once, when it enters view.
   Hover layer is not optional: an SVG chart is interactive by default. */

const NS = 'http://www.w3.org/2000/svg';
const RM = matchMedia('(prefers-reduced-motion: reduce)');
const S = { s1: '#d95926', s2: '#199e70', s3: '#3987e5', s4: '#d55181' };
const INK = '#F2E9E0', MUTED = '#A8988C', FAINT = '#7A6B61', GRID = '#2A221E';
const EMBER = '#E8853A', GOLD = '#E5B54A';

const el = (n, a = {}, p) => {
  const e = document.createElementNS(NS, n);
  for (const k in a) e.setAttribute(k, a[k]);
  if (p) p.appendChild(e);
  return e;
};
const fmt = (v, d = 1) => v.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
const dur = ms => RM.matches ? 0 : ms;
/* Narrow screens get a different layout, not the same one shrunk. A 780-unit
   viewBox on a 350px screen renders 11px type at 5px, which is unreadable. */
const narrow = () => innerWidth < 760;
/* Type size lives in CSS (--vb-fs / --vb-fd on .chart) because a class rule
   beats an SVG presentation attribute. Layout here only needs to know that
   narrow screens get bigger glyphs, so it can leave room for them. */

/* ------------------------------------------------------------------ tooltip */
let tip;
function tooltip() {
  if (!tip) { tip = document.createElement('div'); tip.className = 'tt'; document.body.appendChild(tip); }
  return tip;
}
function showTip(evt, html) {
  const t = tooltip();
  t.innerHTML = html; t.classList.add('on');
  const r = t.getBoundingClientRect();
  let x = evt.clientX + 16, y = evt.clientY - r.height - 12;
  if (x + r.width > innerWidth - 12) x = evt.clientX - r.width - 16;
  if (y < 12) y = evt.clientY + 18;
  t.style.left = x + 'px'; t.style.top = y + 'px';
}
const hideTip = () => tip && tip.classList.remove('on');

function hoverable(node, html) {
  node.style.cursor = 'crosshair';
  node.addEventListener('pointerenter', e => showTip(e, html));
  node.addEventListener('pointermove', e => showTip(e, html));
  node.addEventListener('pointerleave', hideTip);
}

/* ------------------------------------------------------------------ counter */
export function countUp(node, to, { d = 1, suffix = '', prefix = '', ms = 1800 } = {}) {
  if (RM.matches) { node.textContent = prefix + fmt(to, d) + suffix; return; }
  const t0 = performance.now();
  const step = now => {
    const p = Math.min(1, (now - t0) / ms);
    const e = 1 - Math.pow(1 - p, 4);
    node.textContent = prefix + fmt(to * e, d) + suffix;
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

/* ------------------------------------------------ 1. lead times, diverging */
export function leadTimes(mount, rows) {
  const nw = narrow();
  const W = 780, rowH = nw ? 92 : 44, pad = { t: 40, r: nw ? 80 : 30, b: 56, l: nw ? 10 : 240 };
  const H = pad.t + rows.length * rowH + pad.b;
  const max = 78;
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, class: 'chart', role: 'img',
    'aria-label': 'Lead times in months for grid equipment and for semiconductor fabs. They overlap.' }, mount);
  const x = v => pad.l + (v / max) * (W - pad.l - pad.r);

  for (let m = 0; m <= 72; m += 12) {
    el('line', { x1: x(m), x2: x(m), y1: pad.t - 10, y2: H - pad.b + 4, class: 'gl' }, svg);
    const t = el('text', { x: x(m), y: H - pad.b + 20, class: 'ax', 'text-anchor': 'middle' }, svg);
    t.textContent = m === 0 ? '0' : m;
  }
  const at = el('text', { x: x(36), y: 14, class: 'ax-title', 'text-anchor': 'middle' }, svg);
  at.textContent = 'months';

  rows.forEach((r, i) => {
    const y = pad.t + i * rowH + 8;
    const col = r.cls === 'fab' ? S.s3 : S.s1;
    const lab = el('text', nw
      ? { x: pad.l, y: y - 8, class: 'ax', fill: INK }
      : { x: pad.l - 14, y: y + 14, class: 'ax', 'text-anchor': 'end', fill: INK }, svg);
    lab.textContent = r.label;
    const w = x(r.months) - x(0);
    const bar = el('rect', { x: x(0), y, width: 0, height: nw ? 24 : 19, rx: 4, fill: col, opacity: .92 }, svg);
    hoverable(bar, `<b>${r.label}</b>${r.months} months · ${(r.months / 12).toFixed(1)} years`);
    const v = el('text', { x: x(r.months) + 9, y: y + (nw ? 18 : 14), class: 'dl', opacity: 0 }, svg);
    v.textContent = r.months;
    setTimeout(() => {
      bar.style.transition = `width ${dur(1000)}ms cubic-bezier(.16,1,.3,1)`;
      bar.setAttribute('width', w);
      v.style.transition = `opacity ${dur(500)}ms ease ${dur(700)}ms`; v.setAttribute('opacity', 1);
    }, dur(90 * i));
  });

  const band = el('rect', { x: x(29), y: pad.t - 6, width: x(48) - x(29), height: rows.length * rowH + 4,
    fill: EMBER, opacity: 0 }, svg);
  setTimeout(() => { band.style.transition = `opacity ${dur(900)}ms ease`; band.setAttribute('opacity', .07); }, dur(900));
  const bl = el('text', { x: x(38.5), y: pad.t - 12, class: 'ax', fill: EMBER, 'text-anchor': 'middle', opacity: 0 }, svg);
  bl.textContent = 'both sides live here';
  setTimeout(() => { bl.style.transition = `opacity ${dur(700)}ms ease`; bl.setAttribute('opacity', 1); }, dur(1200));
}

/* ------------------------------------------------- 2. price line, drawn */
export function priceLine(mount, d) {
  const nw = narrow();
  const W = 780, H = 360, pad = { t: 26, r: 60, b: 46, l: 52 };
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, class: 'chart', role: 'img',
    'aria-label': 'H100 rental price per GPU-hour, 2023 to 2026. It bottomed in December 2025 and has risen since.' }, mount);
  const pts = d.series, n = pts.length;
  const yMax = 8.5;
  const x = i => pad.l + (i / (n - 1)) * (W - pad.l - pad.r);
  const y = v => H - pad.b - (v / yMax) * (H - pad.t - pad.b);

  for (let v = 0; v <= 8; v += 2) {
    el('line', { x1: pad.l, x2: W - pad.r, y1: y(v), y2: y(v), class: 'gl' }, svg);
    const t = el('text', { x: pad.l - 10, y: y(v) + 4, class: 'ax', 'text-anchor': 'end' }, svg);
    t.textContent = '$' + v;
  }
  pts.forEach((p, i) => {
    if (i % 2) return;
    const t = el('text', { x: x(i), y: H - pad.b + 20, class: 'ax', 'text-anchor': 'middle' }, svg);
    t.textContent = p.t.slice(0, 4) === pts[Math.max(0, i - 2)].t.slice(0, 4) && i ? p.t.slice(5) : p.t.slice(0, 4);
  });

  // full-cost recovery band — the floor the model predicted
  const fc = d.full_cost;
  const bt = y(fc['4']), bb = y(fc['6']);
  el('rect', { x: pad.l, y: bt, width: W - pad.l - pad.r, height: bb - bt,
    fill: S.s2, opacity: .16 }, svg);
  const fcl = el('text', { x: W - pad.r + 6, y: (bt + bb) / 2 + 4, class: 'ax', fill: S.s2 }, svg);
  fcl.textContent = 'full cost';

  const dpath = pts.map((p, i) => `${i ? 'L' : 'M'}${x(i)},${y(p.h100)}`).join(' ');
  const line = el('path', { d: dpath, fill: 'none', stroke: S.s1, 'stroke-width': 2.5,
    'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, svg);
  const L = line.getTotalLength();
  line.style.strokeDasharray = L; line.style.strokeDashoffset = L;
  requestAnimationFrame(() => {
    line.style.transition = `stroke-dashoffset ${dur(2200)}ms cubic-bezier(.16,1,.3,1)`;
    line.style.strokeDashoffset = 0;
  });

  pts.forEach((p, i) => {
    const c = el('circle', { cx: x(i), cy: y(p.h100), r: 5, fill: S.s1,
      stroke: '#14100E', 'stroke-width': 2, opacity: 0 }, svg);
    hoverable(c, `<b>${p.t}</b>$${p.h100.toFixed(2)} / GPU-hour`);
    setTimeout(() => { c.style.transition = `opacity ${dur(360)}ms ease`; c.setAttribute('opacity', 1); },
      dur(2200 * (i / n) + 260));
  });

  const ti = pts.findIndex(p => p.t === d.trough.t);
  const tg = el('g', { opacity: 0 }, svg);
  el('line', { x1: x(ti), x2: x(ti), y1: y(d.trough.v) - 14, y2: y(d.trough.v) - 46,
    stroke: GOLD, 'stroke-width': 1.5, 'stroke-dasharray': '3 3' }, tg);
  const tl = el('text', { x: x(ti), y: y(d.trough.v) - 54, class: 'dl', fill: GOLD, 'text-anchor': 'middle' }, tg);
  tl.textContent = `trough $${d.trough.v.toFixed(2)}`;
  const tl2 = el('text', { x: x(ti), y: y(d.trough.v) - 38, class: 'ax', fill: GOLD, 'text-anchor': 'middle' }, tg);
  tl2.textContent = `then +${Math.round(d.rise * 100)}%`;
  setTimeout(() => { tg.style.transition = `opacity ${dur(700)}ms ease`; tg.setAttribute('opacity', 1); }, dur(2400));
}

/* ------------------------------------- 3. depreciation crossover (the money) */
export function depreciation(mount, d) {
  const nw = narrow();
  const W = 780, H = 400, pad = { t: 26, r: 48, b: 48, l: 58 };
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, class: 'chart', role: 'img',
    'aria-label': 'Straight-line book value against exponential resale decay. The curves cross at about 1.4 years, after which early retirement books a gain.' }, mount);
  const XMAX = 9;
  const x = a => pad.l + (a / XMAX) * (W - pad.l - pad.r);
  const y = v => H - pad.b - v * (H - pad.t - pad.b);

  for (let v = 0; v <= 1.0001; v += 0.25) {
    el('line', { x1: pad.l, x2: W - pad.r, y1: y(v), y2: y(v), class: 'gl' }, svg);
    const t = el('text', { x: pad.l - 10, y: y(v) + 4, class: 'ax', 'text-anchor': 'end' }, svg);
    t.textContent = Math.round(v * 100) + '%';
  }
  for (let a = 0; a <= XMAX; a += 3) {
    const t = el('text', { x: x(a), y: H - pad.b + 20, class: 'ax', 'text-anchor': 'middle' }, svg);
    t.textContent = a + 'y';
  }

  const path = arr => arr.filter(p => p.age <= XMAX).map((p, i) => `${i ? 'L' : 'M'}${x(p.age)},${y(p.v)}`).join(' ');
  const bookD = path(d.book), resD = path(d.resale);

  // the gain region: resale above book, after the crossover
  const gain = d.resale.filter(p => p.age >= d.crossover_age && p.age <= 6);
  const bookAt = a => Math.max(0, 1 - a / 6);
  const area = gain.map((p, i) => `${i ? 'L' : 'M'}${x(p.age)},${y(p.v)}`).join(' ')
    + ' ' + gain.slice().reverse().map(p => `L${x(p.age)},${y(bookAt(p.age))}`).join(' ') + ' Z';
  const clip = el('clipPath', { id: 'gclip' }, svg);
  const cr = el('rect', { x: pad.l, y: 0, width: 0, height: H }, clip);
  el('path', { d: area, fill: S.s2, opacity: .18, 'clip-path': 'url(#gclip)' }, svg);

  const mk = (dd, col, w) => {
    const p = el('path', { d: dd, fill: 'none', stroke: col, 'stroke-width': w, 'stroke-linecap': 'round' }, svg);
    const L = p.getTotalLength(); p.style.strokeDasharray = L; p.style.strokeDashoffset = L;
    requestAnimationFrame(() => {
      p.style.transition = `stroke-dashoffset ${dur(1900)}ms cubic-bezier(.16,1,.3,1)`;
      p.style.strokeDashoffset = 0;
    });
    return p;
  };
  mk(bookD, S.s3, 2.5);
  mk(resD, S.s1, 2.5);
  setTimeout(() => { cr.style.transition = `width ${dur(1100)}ms cubic-bezier(.16,1,.3,1)`;
    cr.setAttribute('width', W); }, dur(1600));

  const lb = el('text', { x: x(6) + 8, y: y(0) - 2, class: 'dl', fill: S.s3 }, svg);
  lb.textContent = '6-yr straight line';
  const lr = el('text', { x: x(8) + 8, y: y(Math.pow(0.83, 8)) + 4, class: 'dl', fill: S.s1 }, svg);
  lr.textContent = 'market resale';

  // crossover marker
  const cx = x(d.crossover_age), cy = y(bookAt(d.crossover_age));
  const cg = el('g', { opacity: 0 }, svg);
  el('circle', { cx, cy, r: 6, fill: 'none', stroke: GOLD, 'stroke-width': 2 }, cg);
  const ct = el('text', { x: cx + 14, y: cy - 12, class: 'dl', fill: GOLD }, cg);
  ct.textContent = 'curves cross · 1.4y';
  setTimeout(() => { cg.style.transition = `opacity ${dur(700)}ms ease`; cg.setAttribute('opacity', 1); }, dur(2100));

  const gt = el('text', { x: x(4.1), y: y(0.30), class: 'dl', fill: S.s2, 'text-anchor': 'middle', opacity: 0 }, svg);
  gt.textContent = 'retiring here books a GAIN';
  setTimeout(() => { gt.style.transition = `opacity ${dur(700)}ms ease`; gt.setAttribute('opacity', 1); }, dur(2500));

  d.observed.forEach((o, i) => {
    const ox = x(o.age), oy = y(o.v);
    const g = el('g', { opacity: 0 }, svg);
    el('path', { d: `M${ox},${oy - 7}L${ox + 7},${oy}L${ox},${oy + 7}L${ox - 7},${oy}Z`,
      fill: GOLD, stroke: '#14100E', 'stroke-width': 1.5 }, g);
    hoverable(g, `<b>${o.part}</b>${(o.v * 100).toFixed(1)}% of cost at ${o.age} years<br>book value ${(bookAt(o.age) * 100).toFixed(1)}% · n=${o.n}`);
    setTimeout(() => { g.style.transition = `opacity ${dur(500)}ms ease`; g.setAttribute('opacity', 1); }, dur(2700 + i * 160));
  });
}

/* ---------------------------------------------------------------- 4. funnel */
export function funnel(mount, rows) {
  const nw = narrow();
  const W = 780, rowH = nw ? 118 : 62, pad = { t: 16, r: 24, b: 24, l: 14 };
  const H = pad.t + rows.length * rowH + pad.b;
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, class: 'chart', role: 'img',
    'aria-label': 'ERCOT large-load funnel: 445.8 GW of applications against 5.9 GW actually energized.' }, mount);
  const max = rows[0].gw, full = W - pad.l - pad.r;
  rows.forEach((r, i) => {
    const y = pad.t + i * rowH;
    const w = Math.max(3, (r.gw / max) * full);
    const col = r.terminal ? EMBER : S.s3;
    const bar = el('rect', { x: pad.l, y, width: 0, height: nw ? 34 : 30, rx: 4, fill: col,
      opacity: r.terminal ? 1 : .55 }, svg);
    hoverable(bar, `<b>${r.label}</b>${fmt(r.gw, 1)} GW · ${((r.gw / max) * 100).toFixed(1)}% of applications`);
    const lab = el('text', { x: pad.l, y: y + (nw ? 62 : 48), class: 'ax',
      fill: r.terminal ? EMBER : MUTED }, svg);
    lab.textContent = r.label;
    const val = el('text', { x: pad.l + 6, y: y + (nw ? 24 : 21), class: 'dl',
      fill: r.terminal ? '#1a0f06' : INK, opacity: 0 }, svg);
    val.textContent = fmt(r.gw, 1) + ' GW';
    setTimeout(() => {
      bar.style.transition = `width ${dur(1100)}ms cubic-bezier(.16,1,.3,1)`;
      bar.setAttribute('width', w);
      val.style.transition = `opacity ${dur(400)}ms ease ${dur(600)}ms`;
      val.setAttribute('opacity', 1);
      if (r.terminal) val.setAttribute('x', pad.l + w + 9), val.setAttribute('fill', EMBER);
    }, dur(140 * i));
  });
}

/* ----------------------------------------------------------- 5. sobol bars */
export function sobol(mount, rows) {
  const nw = narrow();
  const W = 780, rowH = nw ? 128 : 52, pad = { t: 20, r: nw ? 96 : 70, b: 56, l: nw ? 10 : 300 };
  const H = pad.t + rows.length * rowH + pad.b;
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, class: 'chart', role: 'img',
    'aria-label': 'Sobol total-effect indices. The two largest factors have no published measurement.' }, mount);
  const max = 0.4, x = v => pad.l + (v / max) * (W - pad.l - pad.r);
  for (let v = 0; v <= 0.4001; v += 0.1) {
    el('line', { x1: x(v), x2: x(v), y1: pad.t, y2: H - pad.b + 2, class: 'gl' }, svg);
    const t = el('text', { x: x(v), y: H - pad.b + 18, class: 'ax', 'text-anchor': 'middle' }, svg);
    t.textContent = v.toFixed(1);
  }
  const at = el('text', { x: x(0.2), y: H - 4, class: 'ax-title', 'text-anchor': 'middle' }, svg);
  at.textContent = 'total-effect index';

  rows.forEach((r, i) => {
    const y = pad.t + i * rowH + 8;
    const col = r.sourced ? S.s3 : S.s1;
    const lab = el('text', nw
      ? { x: pad.l, y: y - 40, class: 'ax', fill: r.sourced ? MUTED : INK }
      : { x: pad.l - 14, y: y + 14, class: 'ax', 'text-anchor': 'end', fill: r.sourced ? MUTED : INK }, svg);
    lab.textContent = r.k;
    if (!r.sourced) {
      const w2 = el('text', nw
        ? { x: pad.l, y: y - 10, class: 'ax', fill: EMBER }
        : { x: pad.l - 14, y: y + 29, class: 'ax', 'text-anchor': 'end', fill: EMBER }, svg);
      w2.textContent = 'no published measurement';
    }
    const bar = el('rect', { x: pad.l, y, width: 0, height: nw ? 26 : 21, rx: 4, fill: col,
      opacity: r.sourced ? .6 : 1 }, svg);
    hoverable(bar, `<b>${r.k}</b>total-effect ${r.st.toFixed(3)}<br>${r.sourced ? 'sourced' : 'UNSOURCED'}`);
    const v = el('text', { x: x(r.st) + 9, y: y + (nw ? 19 : 16), class: 'dl', fill: col, opacity: 0 }, svg);
    v.textContent = r.st.toFixed(3);
    setTimeout(() => {
      bar.style.transition = `width ${dur(1000)}ms cubic-bezier(.16,1,.3,1)`;
      bar.setAttribute('width', x(r.st) - pad.l);
      v.style.transition = `opacity ${dur(400)}ms ease ${dur(650)}ms`; v.setAttribute('opacity', 1);
    }, dur(110 * i));
  });
}

/* -------------------------------------------------------- 6. density (MC) */
export function density(mount, d) {
  const nw = narrow();
  const W = 780, H = 320, pad = { t: 24, r: 28, b: 46, l: 28 };
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, class: 'chart', role: 'img',
    'aria-label': 'Monte Carlo distribution of the annual shortfall. 80.2% of the mass is above zero.' }, mount);
  const e = d.density.edges, v = d.density.values;
  const xmin = e[0], xmax = e[e.length - 1];
  const vmax = Math.max(...v);
  const x = t => pad.l + ((t - xmin) / (xmax - xmin)) * (W - pad.l - pad.r);
  const y = t => H - pad.b - (t / vmax) * (H - pad.t - pad.b);

  for (let t = -6; t <= 10; t += 2) {
    el('line', { x1: x(t), x2: x(t), y1: pad.t, y2: H - pad.b, class: 'gl' }, svg);
    const l = el('text', { x: x(t), y: H - pad.b + 20, class: 'ax', 'text-anchor': 'middle' }, svg);
    l.textContent = t > 0 ? '+' + t : t;
  }
  const at = el('text', { x: x(2), y: H - 6, class: 'ax-title', 'text-anchor': 'middle' }, svg);
  at.textContent = 'annual shortfall, GW per year';

  const mkArea = (from, to, col, op) => {
    let dd = '';
    for (let i = 0; i < v.length; i++) {
      const c = (e[i] + e[i + 1]) / 2;
      if (c < from || c > to) continue;
      dd += (dd ? 'L' : 'M') + x(c) + ',' + y(v[i]);
    }
    if (!dd) return null;
    const lastC = Math.min(to, xmax), firstC = Math.max(from, xmin);
    dd += `L${x(lastC)},${y(0)}L${x(firstC)},${y(0)}Z`;
    return el('path', { d: dd, fill: col, opacity: op }, svg);
  };
  const clip = el('clipPath', { id: 'dclip' }, svg);
  const cr = el('rect', { x: 0, y: H, width: W, height: 0 }, clip);
  const g = el('g', { 'clip-path': 'url(#dclip)' }, svg);
  const a1 = mkArea(xmin, 0, S.s3, .35); const a2 = mkArea(0, xmax, S.s1, .55);
  [a1, a2].forEach(a => a && g.appendChild(a));
  requestAnimationFrame(() => {
    cr.style.transition = `height ${dur(1500)}ms cubic-bezier(.16,1,.3,1), y ${dur(1500)}ms cubic-bezier(.16,1,.3,1)`;
    cr.setAttribute('y', 0); cr.setAttribute('height', H);
  });

  el('line', { x1: x(0), x2: x(0), y1: pad.t - 6, y2: H - pad.b, stroke: INK,
    'stroke-width': 1.5, 'stroke-dasharray': '4 4', opacity: .6 }, svg);
  const z = el('text', { x: x(0) - 8, y: pad.t + 4, class: 'ax', fill: INK, 'text-anchor': 'end' }, svg);
  z.textContent = 'supply meets demand';

  const pc = el('text', { x: x(4.2), y: pad.t + 44, 'text-anchor': 'middle',
    fill: EMBER, opacity: 0, style: 'font-family:Fraunces,serif;font-weight:700;font-size:38px;letter-spacing:-0.03em' }, svg);
  pc.textContent = Math.round(d.p_regime_c * 1000) / 10 + '%';
  const pl = el('text', { x: x(4.2), y: pad.t + 64, class: 'ax', fill: EMBER, 'text-anchor': 'middle', opacity: 0 }, svg);
  pl.textContent = 'stranding forced';
  [pc, pl].forEach((n, i) => setTimeout(() => {
    n.style.transition = `opacity ${dur(700)}ms ease`; n.setAttribute('opacity', 1);
  }, dur(1300 + i * 130)));

  const med = d.shortfall_quantiles['50'];
  el('line', { x1: x(med), x2: x(med), y1: y(vmax) - 6, y2: H - pad.b, stroke: GOLD, 'stroke-width': 2 }, svg);
  const ml = el('text', { x: x(med), y: y(vmax) - 12, class: 'dl', fill: GOLD, 'text-anchor': 'middle' }, svg);
  ml.textContent = `median +${med.toFixed(2)}`;
}

/* ------------------------------------------------ 7. reconciliation intervals */
export function reconcile(mount, d) {
  const nw = narrow();
  const W = 780, H = nw ? 360 : 210, pad = { t: 46, r: nw ? 96 : 40, b: 62, l: nw ? 10 : 250 };
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, class: 'chart', role: 'img',
    'aria-label': 'Two independent estimates of US AI capacity additions, and where they overlap.' }, mount);
  const max = 14, x = v => pad.l + (v / max) * (W - pad.l - pad.r);
  for (let v = 0; v <= 14; v += 2) {
    el('line', { x1: x(v), x2: x(v), y1: pad.t - 12, y2: H - pad.b + 2, class: 'gl' }, svg);
    const t = el('text', { x: x(v), y: H - pad.b + 18, class: 'ax', 'text-anchor': 'middle' }, svg);
    t.textContent = v;
  }
  const at = el('text', { x: x(7), y: H - 4, class: 'ax-title', 'text-anchor': 'middle' }, svg);
  at.textContent = 'GW per year of US AI capacity additions';

  const [olo, ohi] = d.overlap;
  const ov = el('rect', { x: x(olo), y: pad.t - 10, width: 0, height: nw ? 214 : 92, fill: S.s2, opacity: .18 }, svg);
  setTimeout(() => { ov.style.transition = `width ${dur(900)}ms cubic-bezier(.16,1,.3,1)`;
    ov.setAttribute('width', x(ohi) - x(olo)); }, dur(900));

  d.routes.forEach((r, i) => {
    const y = pad.t + i * (nw ? 106 : 46);
    const col = i ? S.s1 : S.s3;
    const lab = el('text', nw
      ? { x: pad.l, y: y - 8, class: 'ax', fill: INK }
      : { x: pad.l - 14, y: y + 14, class: 'ax', 'text-anchor': 'end', fill: INK }, svg);
    lab.textContent = r.name;
    const bar = el('rect', { x: x(r.lo), y: y + 2, width: 0, height: nw ? 24 : 17, rx: 4, fill: col, opacity: .9 }, svg);
    hoverable(bar, `<b>${r.name}</b>${r.lo} – ${r.hi} GW/yr`);
    const v = el('text', { x: x(r.hi) + 9, y: y + (nw ? 19 : 15), class: 'dl', fill: col, opacity: 0 }, svg);
    v.textContent = `${r.lo}–${r.hi}`;
    setTimeout(() => {
      bar.style.transition = `width ${dur(950)}ms cubic-bezier(.16,1,.3,1)`;
      bar.setAttribute('width', x(r.hi) - x(r.lo));
      v.style.transition = `opacity ${dur(400)}ms ease ${dur(600)}ms`; v.setAttribute('opacity', 1);
    }, dur(160 * i));
  });
  const ol = el('text', { x: (x(olo) + x(ohi)) / 2, y: pad.t + (nw ? 238 : 108), class: 'dl',
    fill: S.s2, 'text-anchor': 'middle', opacity: 0 }, svg);
  ol.textContent = `they agree here — ${olo} to ${ohi} GW/yr`;
  setTimeout(() => { ol.style.transition = `opacity ${dur(700)}ms ease`; ol.setAttribute('opacity', 1); }, dur(1400));
}

/* ------------------------------------------------------- 8. the ASP arithmetic */
export function aspError(mount, d) {
  const nw = narrow();
  const W = 780, H = nw ? 360 : 250, pad = { t: 46, r: 30, b: 56, l: nw ? 20 : 210 };
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, class: 'chart', role: 'img',
    'aria-label': 'The exact implied ASP change is minus 15 percent; the additive shortcut gives minus 30.' }, mount);
  const zero = W - pad.r, scale = (W - pad.l - pad.r) / 0.36;
  const rows = [
    { k: 'Exact  (1+gᵣ)/(1+gᵤ) − 1', v: d.exact, col: S.s2 },
    { k: 'The article’s subtraction', v: d.additive, col: S.s1 },
  ];
  el('line', { x1: zero, x2: zero, y1: pad.t - 16, y2: H - pad.b, stroke: MUTED, 'stroke-width': 1.5 }, svg);
  const zl = el('text', { x: zero, y: pad.t - 22, class: 'ax', 'text-anchor': 'middle' }, svg);
  zl.textContent = '0';

  rows.forEach((r, i) => {
    const y = pad.t + i * (nw ? 128 : 78);
    const w = Math.abs(r.v) * scale;
    const lab = el('text', nw
      ? { x: pad.l, y: y - 10, class: 'ax', fill: INK }
      : { x: pad.l - 16, y: y + 24, class: 'ax', 'text-anchor': 'end', fill: INK }, svg);
    lab.textContent = r.k;
    const bar = el('rect', { x: zero, y, width: 0, height: 34, rx: 4, fill: r.col }, svg);
    hoverable(bar, `<b>${r.k}</b>${(r.v * 100).toFixed(1)}% implied ASP change`);
    const val = el('text', { x: zero - w - 12, y: y + 24, class: 'dl', fill: r.col,
      'text-anchor': 'end', opacity: 0, style: 'font-size:17px;font-weight:600' }, svg);
    val.textContent = (r.v * 100).toFixed(0) + '%';
    setTimeout(() => {
      bar.style.transition = `width ${dur(1000)}ms cubic-bezier(.16,1,.3,1), x ${dur(1000)}ms cubic-bezier(.16,1,.3,1)`;
      bar.setAttribute('width', w); bar.setAttribute('x', zero - w);
      val.style.transition = `opacity ${dur(450)}ms ease ${dur(700)}ms`; val.setAttribute('opacity', 1);
    }, dur(220 * i));
  });
  const note = el('text', { x: pad.l, y: H - 12, class: 'ax', fill: EMBER, opacity: 0 }, svg);
  note.textContent = 'the shortcut overstates the decline by exactly 2×';
  setTimeout(() => { note.style.transition = `opacity ${dur(700)}ms ease`; note.setAttribute('opacity', 1); }, dur(1500));
}
