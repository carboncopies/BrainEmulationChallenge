// Deterministic SYNTHETIC dataset, for UI testing only. Not real data.
const fs = require('fs'), path = require('path');
let s = 12345; const rnd = () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296;
const regions = ['CA1', 'CA3', 'DG', 'EC'].map(id => ({ id, name: id }));
const centers = { CA1: [-80, 0, 0], CA3: [80, 0, 0], DG: [0, 90, 0], EC: [0, -90, 40] };
const neurons = [];
for (const r of regions) for (let k = 0; k < 60; k++) {
  const c = centers[r.id];
  neurons.push({ id: neurons.length, x: c[0] + (rnd() - .5) * 90, y: c[1] + (rnd() - .5) * 90, z: c[2] + (rnd() - .5) * 90, r: 6 + rnd() * 4,
    type: rnd() < 0.2 ? 'interneuron' : 'pyramidal', region: r.id });
}
const conns = [];
for (const a of neurons) for (const b of neurons) {
  if (a.id === b.id) continue;
  const d = Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
  if (rnd() < 0.5 * Math.exp(-d / 60) * (b.type === 'interneuron' ? 1.2 : 0.6)) {
    const gaba = a.type === 'interneuron';
    const nr = 1 + Math.floor(rnd() * 15);
    conns.push({ pre: a.id, post: b.id, receptor: gaba ? 'GABA' : 'AMPA', n_receptors: nr, g_peak_sum: +(nr * (gaba ? 0.4 : 1) * (0.5 + rnd())).toFixed(3) });
  }
}
const dice = { note: 'SYNTHETIC DiCE-style suggestion', parameters: [
  { name: 'growdays', current: 20, suggested: 26, unit: 'days' },
  { name: 'pyr_pyr_gpeak', current: 0.2, suggested: 0.31, unit: 'nS' },
  { name: 'int_pyr_gpeak', current: 0.4, suggested: 0.35, unit: 'nS' },
  { name: 'axon_branch_prob', current: 0.5, suggested: 0.62 } ] };
const out = { id: 'synthetic-demo', title: 'SYNTHETIC demo (UI testing only, not real)', kind: 'synthetic', source: 'make_synthetic.js (seeded LCG)', regions, neurons, connections: conns, dice };
fs.mkdirSync(path.join(__dirname, 'data'), { recursive: true });
fs.writeFileSync(path.join(__dirname, 'data', 'synthetic-demo.json'), JSON.stringify(out));
console.log('synthetic', neurons.length, conns.length);
