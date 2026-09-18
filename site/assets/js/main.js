/* Orchestration: load the model's own figures, populate, reveal, draw once. */
import * as C from './charts.js';

const RM = matchMedia('(prefers-reduced-motion: reduce)');
const $ = s => document.querySelector(s);
const pct = v => (v * 100).toFixed(1) + '%';

const ICON = {
  true:    '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M2.5 8.5l3.5 3.5 7.5-8"/></svg>',
  partial: '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M3 8h10"/></svg>',
  false:   '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M3.5 3.5l9 9M12.5 3.5l-9 9"/></svg>'
};
const LABEL = { true: 'stands', partial: 'partly', false: 'falsified' };

const data = await fetch('data/figures.json').then(r => r.json());

/* ------------------------------------------------------------- hero + stats */
$('#np').textContent = data.meta.parameters;
$('#nh').textContent = data.meta.hard_evidence;
$('#mcn').textContent = data.verdict.n.toLocaleString('en-US');

/* ------------------------------------------------------------- scoreboard */
$('#score').innerHTML = data.claims.map(c => `
  <div class="claim">
    <div class="claim-id">${c.id}</div>
    <div class="claim-text">${c.text}</div>
    <div class="tag ${c.verdict}">${ICON[c.verdict]}<span>${LABEL[c.verdict]}</span></div>
    <p class="claim-note">${c.note}</p>
  </div>`).join('');

/* ---------------------------------------------------------------- regimes */
$('#regimes').innerHTML = data.regimes.map(r => `
  <div class="regime ${r.key.toLowerCase()} ${r.key === 'C' ? 'hit' : ''}">
    <div class="regime-key">${r.key}</div>
    <div class="regime-cond">${r.cond}</div>
    <h3>${r.name}</h3>
    <p>${r.body}</p>
    ${r.key === 'C' ? `<div class="regime-flag">where the evidence points · ${pct(data.verdict.p_regime_c)}</div>` : ''}
  </div>`).join('');

/* --------------------------------------------------------------- unknowns */
$('#unknowns').innerHTML = data.unknowns.map(u => `<li style="margin-bottom:0.8rem">${u}</li>`).join('');

/* ------------------------------------------------------------- stat values */
const P = data.prices;
$('#s-cash').textContent = '$' + P.cash_cost.toFixed(2);
$('#s-energy').textContent = Math.round(P.energy_share * 100) + '%';
$('#s-rise').textContent = '+' + (P.rise * 100).toFixed(1) + '%';
$('#s-p').textContent = pct(data.verdict.p_regime_c);
$('#s-short').textContent = '+' + data.verdict.median_shortfall_gw.toFixed(2);
$('#s-strand').textContent = pct(data.verdict.median_stranded_share);

/* ------------------------------------------------------------ hero kinetic */
const p = data.verdict.p_regime_c;
requestAnimationFrame(() => {
  setTimeout(() => {
    C.countUp($('#pv'), p * 100, { d: 1, suffix: '%', ms: 2100 });
    $('#pf').style.width = (p * 100) + '%';
  }, RM.matches ? 0 : 420);
});

/* --------------------------------------------------- reveal + draw-on-enter */
const drawn = new WeakSet();
const CHARTS = [
  ['#lead',    m => C.leadTimes(m, data.lead_times)],
  ['#price',   m => C.priceLine(m, data.prices)],
  ['#depr',    m => C.depreciation(m, data.depreciation)],
  ['#funnel',  m => C.funnel(m, data.funnel)],
  ['#sobol',   m => C.sobol(m, data.sobol)],
  ['#density', m => C.density(m, data.verdict)],
  ['#recon',   m => C.reconcile(m, data.reconciliation)],
  ['#asp',     m => C.aspError(m, data.asp)],
];

const io = new IntersectionObserver((entries, obs) => {
  for (const e of entries) {
    if (!e.isIntersecting) continue;
    e.target.classList.add('in');
    const hit = CHARTS.find(([sel]) => e.target.matches(sel) || e.target.querySelector(sel));
    if (hit) {
      const mount = e.target.matches(hit[0]) ? e.target : e.target.querySelector(hit[0]);
      if (mount && !drawn.has(mount)) { drawn.add(mount); hit[1](mount); }
    }
    obs.unobserve(e.target);
  }
}, { rootMargin: '0px 0px -12% 0px', threshold: 0.12 });

document.querySelectorAll('.rise').forEach(n => io.observe(n));
CHARTS.forEach(([sel]) => { const n = $(sel); if (n) io.observe(n); });

/* Anything already in view on load should not wait for a scroll event. */
addEventListener('load', () => {
  document.querySelectorAll('.rise').forEach(n => {
    const r = n.getBoundingClientRect();
    if (r.top < innerHeight * 0.92) n.classList.add('in');
  });
});
