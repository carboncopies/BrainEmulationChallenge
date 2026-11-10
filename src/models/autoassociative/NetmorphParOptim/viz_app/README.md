# Netmorph reservoir viewer

Node (Express) backend + static Three.js frontend (no build step, no CDN; three is served from node_modules).

## Run
    npm install
    npm start                 # http://localhost:3100  (PORT env overrides; avoid 8000/8001/7999)
    PORT=3150 DATA_DIR=/path/a:/path/b npm start   # DATA_DIR: ':'-separated dirs of run *.json (default ./data)
    npm test                  # starts server, validates API + that app.js parses

Endpoints: `GET /api/health`, `GET /api/runs` (metadata list), `GET /api/runs/:id` (run + computed `summary`), `GET /api/runs/:id/dice`.

## Data
- `convert_pickles.py`: converts the autoassociative pickles (read-only) to `data/real-autoassociative.json`. Needs numpy>=2:
  `<venv>/bin/python -I convert_pickles.py [--src DIR] [--out FILE] [--regions N]`. Pickles carry no region labels, so regions are derived z-slabs.
- `make_synthetic.js`: writes `data/synthetic-demo.json` (SYNTHETIC, UI testing only).
- Files starting with `_` are ignored. To use the Netmorph agent's output, point `DATA_DIR` at its `viz_data/` (must match the schema below, or adapt).

## Run JSON schema (one file per run; id = filename)
    { "id", "title", "kind": "real"|"synthetic", "source", "notes",
      "regions": [{"id","name"}],                      // optional; else taken from neurons[].region
      "neurons": [{"id","x","y","z","r","type":"pyramidal"|"interneuron"|"unknown","region"}],
      "connections": [{"pre","post","receptor":"AMPA"|"GABA","g_peak_sum","n_receptors"}],  // one row per pre->post pair
      "dice": <optional, see below> }
Connection class = pre type + post type + receptor (Pyr->Pyr AMPA, Pyr->Int AMPA, Int->Pyr GABA, Int->Int GABA).
DiCE: `dice` in the run, or sidecar `<dir>/dice/<id>.json` / `<dir>/<id>.dice.json`, or paste into the UI. Accepted shapes:
`{parameters:[{name,current,suggested,...}]}`, a bare array of objects, or `{name:{current,suggested}}`/`{name:value}`. Any columns are shown.
