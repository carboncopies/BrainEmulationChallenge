import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const $ = id => document.getElementById(id);
const CLS = { 'Pyr->Pyr AMPA': 0x4da3ff, 'Pyr->Int AMPA': 0x3fd0c9, 'Int->Pyr GABA': 0xff7a59, 'Int->Int GABA': 0xd16ba5 };
const TYPE_COL = { pyramidal: 0x4da3ff, interneuron: 0xff7a59, unknown: 0x9aa0a6 };
const REG_PAL = [0xe6c229, 0x6bd490, 0xb48cff, 0xff9fb2, 0x5dd0e8, 0xc9a66b, 0x9ad14d, 0xf08a4b];
const short = t => (t === 'pyramidal' ? 'Pyr' : t === 'interneuron' ? 'Int' : 'Unk');
const fmt = v => (Math.abs(v) >= 100 ? v.toFixed(0) : v.toPrecision(3)).replace(/\.?0+$/, m => m.includes('.') ? '' : m);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

let webgl = true, run = null, scene, camera, renderer, controls, nodeGroup, edgeGroup, nodeMeshes = [];
const enabled = new Set(Object.keys(CLS));

function initThree() {
  const canvas = $('c');
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  scene = new THREE.Scene(); scene.background = new THREE.Color(0x0b0e13);
  camera = new THREE.PerspectiveCamera(50, 1, 0.1, 5000);
  scene.add(new THREE.AmbientLight(0xffffff, 0.6));
  const dl = new THREE.DirectionalLight(0xffffff, 1.2); dl.position.set(1, 2, 3); scene.add(dl);
  controls = new OrbitControls(camera, canvas); controls.enableDamping = true;
  nodeGroup = new THREE.Group(); edgeGroup = new THREE.Group(); scene.add(nodeGroup, edgeGroup);
  const resize = () => { const w = $('canvasWrap').clientWidth, h = $('canvasWrap').clientHeight; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); };
  new ResizeObserver(resize).observe($('canvasWrap')); resize();
  const ray = new THREE.Raycaster(), mouse = new THREE.Vector2();
  canvas.addEventListener('pointermove', e => {
    const r = canvas.getBoundingClientRect();
    mouse.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(mouse, camera);
    const h = ray.intersectObjects(nodeMeshes)[0];
    if (h) { const n = h.object.userData.n; $('tip').textContent = `#${n.id} ${n.type} ${n.region || ''}`; }
  });
  (function loop() { requestAnimationFrame(loop); controls.update(); renderer.render(scene, camera); })();
}

function clear(g) { while (g.children.length) { const o = g.children.pop(); o.geometry && o.geometry.dispose(); o.material && o.material.dispose(); } }

function regionColor(r) { const i = (run.regions || []).findIndex(x => x.id === r); return REG_PAL[(i < 0 ? 0 : i) % REG_PAL.length]; }

function drawNodes() {
  clear(nodeGroup); nodeMeshes = [];
  const by = $('colorBy').value;
  const ns = run.neurons; if (!ns.length) return;
  const c = ns.reduce((a, n) => [a[0] + n.x, a[1] + n.y, a[2] + n.z], [0, 0, 0]).map(v => v / ns.length);
  run._c = c;
  let ext = 1; for (const n of ns) ext = Math.max(ext, Math.hypot(n.x - c[0], n.y - c[1], n.z - c[2]));
  run._ext = ext;
  const rs = ns.map(n => n.r || 5), rmean = rs.reduce((a, b) => a + b, 0) / rs.length;
  const sc = Math.min(1, ext / 12 / rmean) ; // keep spheres modest
  for (const n of ns) {
    const col = by === 'region' ? regionColor(n.region) : (TYPE_COL[n.type] || TYPE_COL.unknown);
    const m = new THREE.Mesh(new THREE.SphereGeometry((n.r || 5) * sc * (n.type === 'interneuron' ? 0.85 : 1), 14, 10), new THREE.MeshStandardMaterial({ color: col }));
    m.position.set(n.x - c[0], n.y - c[1], n.z - c[2]); m.userData.n = n; nodeGroup.add(m); nodeMeshes.push(m);
  }
  run._sc = sc;
}

function drawEdges() {
  clear(edgeGroup);
  const metric = $('metric').value, top = +$('topN').value; $('topNv').textContent = top;
  const byId = new Map(run.neurons.map(n => [n.id, n])), c = run._c;
  let es = run.connections.filter(e => byId.has(e.pre) && byId.has(e.post)).map(e => {
    const a = byId.get(e.pre), b = byId.get(e.post); return { e, a, b, k: `${short(a.type)}->${short(b.type)} ${e.receptor}`, w: e[metric] || 0 };
  }).filter(o => enabled.has(o.k));
  es.sort((x, y) => y.w - x.w); es = es.slice(0, top);
  const wmax = es.length ? es[0].w || 1 : 1, base = run._ext / 400;
  const up = new THREE.Vector3(0, 1, 0), geo = new THREE.CylinderGeometry(1, 1, 1, 5, 1, true);
  const mats = {};
  for (const { a, b, k, w } of es) {
    const p = new THREE.Vector3(a.x - c[0], a.y - c[1], a.z - c[2]), q = new THREE.Vector3(b.x - c[0], b.y - c[1], b.z - c[2]);
    const d = q.clone().sub(p), len = d.length(); if (!len) continue;
    const mat = mats[k] || (mats[k] = new THREE.MeshBasicMaterial({ color: CLS[k] || 0xcccccc, transparent: true, opacity: 0.55 }));
    const m = new THREE.Mesh(geo, mat);
    m.position.copy(p).addScaledVector(d, 0.5); m.scale.set(base * (0.4 + 3 * w / wmax), len, base * (0.4 + 3 * w / wmax));
    m.quaternion.setFromUnitVectors(up, d.normalize()); edgeGroup.add(m);
  }
}

function frame() {
  const e = run._ext || 100; camera.position.set(0, 0, e * 2.6); controls.target.set(0, 0, 0); camera.far = e * 20; camera.updateProjectionMatrix(); controls.update();
}

function renderSummary() {
  const s = run.summary;
  let h = `<p>${s.n_neurons} neurons (${Object.entries(s.typeCounts).map(([k, v]) => `${v} ${esc(k)}`).join(', ')}), ${s.n_connections} connections`;
  if (s.skipped_connections) h += ` (${s.skipped_connections} skipped: unknown neuron id)`;
  h += `</p><table><tr><th>Class</th><th>Conns</th><th>g_peak sum</th><th>Receptors</th></tr>`;
  for (const [k, v] of Object.entries(s.classes)) h += `<tr><td><span class="sw" style="background:#${CLS[k].toString(16)}"></span>${k}</td><td>${v.connections}</td><td>${fmt(v.g_peak_sum)}</td><td>${v.n_receptors || '-'}</td></tr>`;
  if (s.other_classes.connections) h += `<tr><td>other (unknown type)</td><td>${s.other_classes.connections}</td><td>${fmt(s.other_classes.g_peak_sum)}</td><td>${s.other_classes.n_receptors || '-'}</td></tr>`;
  $('counts').innerHTML = h + '</table>';
  $('notes').textContent = run.notes || '';
}

function renderMatrix() {
  const m = run.summary.matrix, k = $('mMetric').value, v = m[k], max = Math.max(1e-12, ...v.flat());
  let h = '<table><tr><th>pre \\ post</th>' + m.regions.map(r => `<th>${esc(r)}</th>`).join('') + '</tr>';
  v.forEach((row, i) => { h += `<tr><td>${esc(m.regions[i])}</td>` + row.map(x => `<td style="background:rgba(77,163,255,${(0.75 * x / max).toFixed(2)})">${x ? fmt(x) : ''}</td>`).join('') + '</tr>'; });
  $('matrix').innerHTML = h + '</table>';
}

function renderLegend() {
  const by = $('colorBy').value;
  const items = by === 'region' ? (run.regions || []).map(r => [regionColor(r.id), `${r.id} (${run.summary.regionCounts[r.id] || 0})`])
    : Object.entries(TYPE_COL).filter(([t]) => run.summary.typeCounts[t]).map(([t, c]) => [c, `${t} (${run.summary.typeCounts[t]})`]);
  $('legend').innerHTML = items.map(([c, t]) => `<span><span class="sw" style="background:#${c.toString(16).padStart(6, '0')}"></span>${esc(t)}</span>`).join('');
}

function renderDice(d) {
  const el = $('dice');
  if (!d) { el.innerHTML = '<p class="muted">No DiCE data for this run. Add <code>dice</code> to the run JSON, a <code>dice/&lt;id&gt;.json</code> sidecar, or paste JSON below.</p>'; return; }
  if (d.error) { el.textContent = 'DiCE error: ' + d.error; return; }
  // accepted: {parameters:[{name,current,suggested,...}]} | [{...}] | {name:{current,suggested}} | {name:value}
  let rows = Array.isArray(d) ? d : Array.isArray(d.parameters) ? d.parameters : Array.isArray(d.suggestions) ? d.suggestions
    : Object.entries(d.parameters || d).filter(([, v]) => typeof v !== 'string' || true).map(([k, v]) => (v && typeof v === 'object' && !Array.isArray(v)) ? { name: k, ...v } : { name: k, suggested: v });
  rows = rows.map(r => (r && typeof r === 'object' && !Array.isArray(r)) ? r : { value: r });
  const cols = [...new Set(rows.flatMap(Object.keys))];
  let h = (d.note ? `<p class="muted">${esc(d.note)}</p>` : '') + '<table><tr>' + cols.map(c => `<th>${esc(c)}</th>`).join('') + '</tr>';
  for (const r of rows) h += '<tr>' + cols.map(c => {
    let v = r[c]; if (v === undefined) return '<td></td>';
    const cls = (c === 'suggested' && typeof v === 'number' && typeof r.current === 'number') ? (v > r.current ? 'up' : v < r.current ? 'down' : '') : '';
    return `<td class="${cls}">${esc(typeof v === 'object' ? JSON.stringify(v) : v)}</td>`;
  }).join('') + '</tr>';
  el.innerHTML = h + '</table>';
}

function toggles() {
  $('classToggles').innerHTML = Object.keys(CLS).map(k => `<label><input type="checkbox" data-k="${k}" ${enabled.has(k) ? 'checked' : ''}><span class="sw" style="background:#${CLS[k].toString(16)}"></span>${k}</label>`).join('');
  $('classToggles').querySelectorAll('input').forEach(i => i.onchange = () => { i.checked ? enabled.add(i.dataset.k) : enabled.delete(i.dataset.k); webgl && drawEdges(); });
}

async function loadRun(id) {
  const r = await fetch('/api/runs/' + encodeURIComponent(id));
  if (!r.ok) { $('counts').textContent = 'Failed to load run: ' + r.status; return; }
  run = await r.json();
  $('badge').textContent = run.kind; $('badge').className = run.kind;
  $('topN').max = Math.max(10, run.connections.length); $('topN').value = Math.min(+$('topN').value || 400, +$('topN').max);
  if (webgl) { drawNodes(); drawEdges(); frame(); }
  renderSummary(); renderMatrix(); renderLegend(); renderDice(run.dice);
}

async function main() {
  try { initThree(); } catch (e) { webgl = false; $('tip').textContent = '3D view unavailable (WebGL failed): tables still work.'; }
  toggles();
  const { runs } = await (await fetch('/api/runs')).json();
  $('runSel').innerHTML = runs.map(r => `<option value="${esc(r.id)}">${esc(r.title || r.id)}</option>`).join('');
  $('runSel').onchange = () => loadRun($('runSel').value);
  $('metric').onchange = $('topN').oninput = () => webgl && drawEdges();
  $('colorBy').onchange = () => { webgl && drawNodes(); renderLegend(); };
  $('mMetric').onchange = renderMatrix;
  $('diceBtn').onclick = () => { try { renderDice(JSON.parse($('diceIn').value)); } catch (e) { $('dice').textContent = 'Invalid JSON: ' + e.message; } };
  if (runs.length) loadRun(runs[0].id); else $('counts').textContent = 'No runs found in data dir.';
}
main().catch(e => { document.body.insertAdjacentHTML('beforeend', '<pre>' + esc(e.stack || e) + '</pre>'); });
