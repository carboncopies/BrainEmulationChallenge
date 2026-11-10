'use strict';
// Minimal backend: serves run JSON from DATA_DIR(s) plus the static frontend.
const express = require('express');
const fs = require('fs');
const path = require('path');

const PORT = parseInt(process.env.PORT || '3100', 10);
// DATA_DIR may be several dirs separated by ':' ; later dirs do not override earlier ids.
const DATA_DIRS = (process.env.DATA_DIR || path.join(__dirname, 'data')).split(':').filter(Boolean).map(d => path.resolve(d));

const CLASSES = ['Pyr->Pyr AMPA', 'Pyr->Int AMPA', 'Int->Pyr GABA', 'Int->Int GABA'];
const short = t => (t === 'pyramidal' ? 'Pyr' : t === 'interneuron' ? 'Int' : 'Unk');

function safeId(id) { return /^[A-Za-z0-9._-]+$/.test(id) && !id.includes('..'); }

function listFiles() {
  const out = new Map();
  for (const dir of DATA_DIRS) {
    let names = [];
    try { names = fs.readdirSync(dir); } catch (e) { continue; }
    for (const n of names) {
      if (!n.endsWith('.json') || n.startsWith('_') || n === 'SCHEMA.json') continue;
      const id = n.slice(0, -5);
      if (safeId(id) && !out.has(id)) out.set(id, { id, file: path.join(dir, n), dir });
    }
  }
  return out;
}

function loadRun(id) {
  const f = listFiles().get(id);
  if (!f) return null;
  const run = JSON.parse(fs.readFileSync(f.file, 'utf8'));
  run.id = run.id || id;
  if (!run.dice) { // sidecar DiCE file: <dir>/dice/<id>.json or <dir>/<id>.dice.json
    for (const c of [path.join(f.dir, 'dice', id + '.json'), path.join(f.dir, id + '.dice.json')]) {
      if (fs.existsSync(c)) { try { run.dice = JSON.parse(fs.readFileSync(c, 'utf8')); } catch (e) { run.dice = { error: String(e) }; } break; }
    }
  }
  return run;
}

function summarize(run) {
  const neurons = run.neurons || [], conns = run.connections || [];
  const byId = new Map(neurons.map(n => [n.id, n]));
  const typeCounts = {};
  for (const n of neurons) typeCounts[n.type] = (typeCounts[n.type] || 0) + 1;
  const regions = (run.regions && run.regions.length) ? run.regions.map(r => r.id)
    : [...new Set(neurons.map(n => n.region || 'all'))];
  const classes = {};
  for (const c of CLASSES) classes[c] = { connections: 0, g_peak_sum: 0, n_receptors: 0 };
  const other = { connections: 0, g_peak_sum: 0, n_receptors: 0 };
  const matrix = { regions, g_peak_sum: regions.map(() => regions.map(() => 0)), n_receptors: regions.map(() => regions.map(() => 0)), connections: regions.map(() => regions.map(() => 0)) };
  let skipped = 0;
  for (const c of conns) {
    const a = byId.get(c.pre), b = byId.get(c.post);
    if (!a || !b) { skipped++; continue; }
    const g = c.g_peak_sum || 0, nr = c.n_receptors || 0;
    const key = `${short(a.type)}->${short(b.type)} ${c.receptor}`;
    const k = classes[key] || other;
    k.connections++; k.g_peak_sum += g; k.n_receptors += nr;
    const i = regions.indexOf(a.region || 'all'), j = regions.indexOf(b.region || 'all');
    if (i >= 0 && j >= 0) { matrix.g_peak_sum[i][j] += g; matrix.n_receptors[i][j] += nr; matrix.connections[i][j]++; }
  }
  const regionCounts = {};
  for (const n of neurons) regionCounts[n.region || 'all'] = (regionCounts[n.region || 'all'] || 0) + 1;
  return { n_neurons: neurons.length, n_connections: conns.length, skipped_connections: skipped, typeCounts, regionCounts, classes, other_classes: other, matrix };
}

function meta(id, run) {
  return { id, title: run.title || id, kind: run.kind || 'unknown', source: run.source || null,
    n_neurons: (run.neurons || []).length, n_connections: (run.connections || []).length, has_dice: !!run.dice };
}

const app = express();
app.use(express.static(path.join(__dirname, 'public')));
app.use('/vendor/three', express.static(path.join(__dirname, 'node_modules', 'three')));

app.get('/api/health', (req, res) => res.json({ ok: true, data_dirs: DATA_DIRS }));
app.get('/api/runs', (req, res) => {
  const runs = [];
  for (const id of listFiles().keys()) {
    try { runs.push(meta(id, loadRun(id))); } catch (e) { runs.push({ id, error: 'unreadable: ' + e.message }); }
  }
  runs.sort((a, b) => (a.kind === 'synthetic') - (b.kind === 'synthetic') || a.id.localeCompare(b.id));
  res.json({ runs });
});
app.get('/api/runs/:id', (req, res) => {
  if (!safeId(req.params.id)) return res.status(400).json({ error: 'bad id' });
  let run; try { run = loadRun(req.params.id); } catch (e) { return res.status(500).json({ error: e.message }); }
  if (!run) return res.status(404).json({ error: 'not found' });
  run.summary = summarize(run);
  res.json(run);
});
app.get('/api/runs/:id/dice', (req, res) => {
  if (!safeId(req.params.id)) return res.status(400).json({ error: 'bad id' });
  let run; try { run = loadRun(req.params.id); } catch (e) { return res.status(500).json({ error: e.message }); }
  if (!run) return res.status(404).json({ error: 'not found' });
  if (!run.dice) return res.status(404).json({ error: 'no dice data for run' });
  res.json(run.dice);
});

if (require.main === module) {
  app.listen(PORT, () => console.log(`netmorph viz on http://localhost:${PORT} (data: ${DATA_DIRS.join(', ')})`));
}
module.exports = { app, summarize };
