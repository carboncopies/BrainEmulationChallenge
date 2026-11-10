// Starts the server on a random port, checks API validity and that page JS parses.
const { spawn } = require('child_process'), fs = require('fs'), path = require('path'), vm = require('vm');
const assert = require('assert');
const port = 3190 + Math.floor(Math.random() * 50);
const root = path.join(__dirname, '..');
// syntax check of ES module frontend (vm.SourceTextModule needs a flag; use node --check on a .mjs copy)
const tmp = path.join(require('os').tmpdir(), 'app_check_' + process.pid + '.mjs');
fs.copyFileSync(path.join(root, 'public/app.js'), tmp);
require('child_process').execFileSync(process.execPath, ['--check', tmp]); fs.unlinkSync(tmp);
console.log('app.js parses');
const srv = spawn(process.execPath, ['server.js'], { cwd: root, env: { ...process.env, PORT: port } });
(async () => {
  await new Promise(r => setTimeout(r, 800));
  const get = async p => { const r = await fetch(`http://localhost:${port}${p}`); return [r.status, r.headers.get('content-type'), await r.text()]; };
  const [, , rj] = await get('/api/runs'); const runs = JSON.parse(rj).runs; assert(runs.length >= 1);
  for (const m of runs) {
    const [st, , body] = await get('/api/runs/' + m.id); assert.equal(st, 200); const r = JSON.parse(body), s = r.summary;
    assert.equal(s.n_neurons, r.neurons.length); assert.equal(s.skipped_connections, 0);
    const tot = Object.values(s.classes).reduce((a, c) => a + c.connections, 0) + s.other_classes.connections; assert.equal(tot, r.connections.length);
    const mt = s.matrix.connections.flat().reduce((a, b) => a + b, 0); assert.equal(mt, r.connections.length);
    console.log('ok run', m.id, s.n_neurons, 'neurons', tot, 'conns', JSON.stringify(Object.fromEntries(Object.entries(s.classes).map(([k, v]) => [k, v.connections]))));
  }
  assert.equal((await get('/api/runs/nope'))[0], 404); assert.equal((await get('/api/runs/..%2Fx'))[0] >= 400, true);
  assert.equal((await get('/'))[0], 200); assert.equal((await get('/vendor/three/build/three.module.js'))[0], 200);
  assert.equal((await get('/vendor/three/examples/jsm/controls/OrbitControls.js'))[0], 200);
  console.log('ALL OK');
})().catch(e => { console.error(e); process.exitCode = 1; }).finally(() => srv.kill());
