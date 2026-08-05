# Autoassociative Optuna — Session Status

_Updated 2026-07-13. Target: the 8-neuron recurrent LIFC autoassociative memory
(Hopfield-style) from `LIFtest.py -Autoassociative`._

## TL;DR — read this first

Phases 1–3 are built and verified. **Nothing has been launched.** The Optuna study is
ready for you to start in tmux.

- **Phase 1 (done):** the circuit shows genuine pattern completion, but **only with
  `-STDP`**, and the recall is transient. The shipped default (no `-STDP`) does no recall
  at all. See "Phase 1 finding" and the bug-adjacent note for Randal below.
- **Decision (confirmed by you): optimize the `-STDP` circuit (Option 1)**, maximizing the
  fraction of cycles with full 4/4 recall while a saturation control keeps a trivial
  all-fire state from gaming the score.
- **Phase 2 (done, verified):** `autoassociative_lifc.py` — a dedicated, parameterized copy
  of the circuit with an inline SCORE readout. Verified **bit-identical** to the original
  `LIFtest.py` at default parameters (both STDP off and on).
- **Phase 3 (done, not run):** `optuna_autoassociative.py` — hardened TPE harness,
  SQLite-persisted, sequential, justified search space. Launch commands below.

## For Randal — the STDP default is bug-adjacent (please confirm intent)

Stated precisely, factually, the same way I flagged the shift-register issues:

- **The shipped default of `LIFtest.py -Autoassociative` does no associative recall at all.**
  Run out of the box, the uncued half of the pattern (neurons 4–7) never fires in the cue
  window — the recurrent synapses have no functional effect; each neuron only echoes its
  own direct stimulation. (Verdict from `phase1_diagnostic.py`: 0/50 recall cycles.)
- **The associative-memory behavior only appears with the `-STDP` flag, which is not the
  default.** With `-STDP`, uncued neurons are recalled by the partial cue (28/50 cycles).
- **Root cause:** every AMPA receptor is created with `STDP_Method='Hebbian'`
  (`LIFtest.py` ~line 351), but the sim-level master switch `SetSTDP(_DoSTDP=Args.STDP)`
  (line 57) defaults **off**, because `-STDP` is a `store_true` flag. So the default
  configures Hebbian receptors and then globally disables the plasticity they need. A
  Hopfield-style memory only completes because Hebbian co-activation during training
  strengthens the recurrent weights; with plasticity off there is no attractor, hence no
  recall.
- **Open question for you:** is STDP-off-by-default intentional (a "no-training" control
  condition, with the real demo meant to be run with `-STDP`), or an oversight? I did **not**
  change it — flagging only. Either way, the optimizer sets the flag explicitly.

## Phase 1 finding — the evidence

Both runs used the default fixed seed (`-Seed 0`), so results are deterministic. The
diagnostic counts spikes of the uncued neurons (4–7) in the cue window vs. the undriven
"quiet" gaps of each 1600 ms cycle. Genuine completion = uncued fire in the cue window but
stay silent in the gaps (silence rules out a saturated all-fire attractor).

**Default (`-Autoassociative`, STDP off):** uncued neurons fire **0** spikes in the cue
window across all 50 cycles; quiet gaps also 0. → **No completion** (inert recurrence).

**With `-STDP`:** uncued neurons recalled by the cue (186 spikes total), quiet gaps 0.
Per-cycle recall trajectory:
```
  cycles  1-6 : 0/4   (Hebbian weights still building)
  cycles  7-34: 4/4   (full completion — attractor formed, stable plateau)
  cycles 35-41: decaying (3,3,3,2,2,2,2)
  cycles 42-50: 0/4   (recall collapsed — likely potentiation runaway then adaptation/
                       fatigue suppressing the uncued cells; not fully pinned down)
```
→ **Genuine completion**, full recall on **28/50 cycles**, silent when undriven. This
rise→plateau→collapse shape is exactly what the optimization targets: widen the plateau
to all cycles.

## Objective (as you specified)

Maximize **`clean_recall`** = fraction of the 50 cycles that are BOTH:
1. **full recall** — every uncued neuron (4–7) fires in the cue window, AND
2. **clean** — every neuron is silent in the two undriven quiet gaps.

Condition 2 is the anti-gaming control: a saturated all-on state fires in the gaps and so
scores **0**, not 1. The control lives in one function, `phase1_diagnostic.score_recall()`,
which is imported by both the CLI diagnostic and the sim's inline scorer — so the "real vs.
fake recall" check in scoring is literally the same code that detects it in diagnosis.
**Baseline (default params) = 0.560 (28/50).** Range is [0, 1]; goal is toward 1.0.

(If you later want a Pareto view, an easy multi-objective variant is {maximize recall
cycles, minimize gap-leak spikes}; single-objective already encodes the leak as a hard
gate, which is stricter.)

## Phase 2 — parameterization & default-identical verification

`autoassociative_lifc.py` is the circuit extracted from `LIFtest.py`'s `-Autoassociative`
branch into a dedicated script (same structure as `shift_register_lifc.py`). The values
that were hardcoded inline are now CLI args, **each defaulting to the original constant**:

| arg | default (= original) | meaning |
|---|---|---|
| `-Weight` | 0.5 | receptor weight, AMPA & NMDA (original tied both at 0.5) |
| `-STDP_A_pos` | 0.027 | AMPA Hebbian potentiation rate |
| `-STDP_A_neg` | 0.02 | AMPA Hebbian depression rate |
| `-STDP_Tau_pos` | 7.0 | AMPA STDP potentiation window (ms) |
| `-STDP_Tau_neg` | 7.0 | AMPA STDP depression window (ms) |
| `-SuperSynapses` | 4 | integer multiplier on receptor quantity |
| `-STDP` | off | plasticity master switch (harness always passes it) |

**Verification (done):** running `autoassociative_lifc.py` at default params produced Vm
traces **bit-identical** to the original `LIFtest.py -Autoassociative`, in BOTH regimes:
- defaults, STDP off  ≡ `LIFtest.py -Autoassociative`      → SCORE clean_recall=0.0000
- defaults, `-STDP`   ≡ `LIFtest.py -Autoassociative -STDP` → SCORE clean_recall=0.5600

So the extraction and parameterization introduce no behavioral drift. `LIFtest.py` itself was
**not modified**.

Note: `-Weight` drives AMPA and NMDA together (original tied them). If you'd rather tune them
separately, splitting into `-WeightAMPA` / `-WeightNMDA` is a one-line change; I kept the
original coupling to stay faithful and keep the search space lower-dimensional.

## Phase 3 — the Optuna harness

`optuna_autoassociative.py`: TPE, single-objective **maximize clean_recall**, SQLite-persisted
(resumable), **sequential** (single local NES — never parallelize, per repo policy). Each
trial runs `autoassociative_lifc.py` once **with `-STDP`** and parses its SCORE line.

Hardening (mirrors the shift-register robust harness):
- A dropped sim (timeout / missing SCORE) is retried up to 3× with 5 s backoff.
- If it still fails it **raises `SimCommsError`** rather than returning 0.0 — a comms
  failure marks the trial FAIL and the study continues, instead of poisoning the search with
  a false zero that a genuine bad-parameter zero is indistinguishable from.
- Per-sim subprocess timeout 120 s (a real run is ~12 s; this catches a true hang).

**Search space & justification** (defaults in brackets; ranges bracket the defaults while
staying physically sane):
| param | range | why |
|---|---|---|
| `Weight` | [0.05, 5.0] log | primary recurrent gain. Too low → inert (no completion, like the STDP-off default); too high → saturation, which the gap control penalizes. Log because it's a gain. |
| `STDP_A_pos` | [0.005, 0.15] | potentiation rate: sets recall-onset speed and, if too strong, the late runaway that collapses recall. |
| `STDP_A_neg` | [0.005, 0.15] | depression rate: the A_pos/A_neg balance is the main lever on plateau stability vs. collapse. |
| `STDP_Tau_pos` | [2.0, 40.0] ms | STDP timing window (AMPA-kinetics ballpark). |
| `STDP_Tau_neg` | [2.0, 40.0] ms | as above. |
| `SuperSynapses` | [1, 8] int | integer coupling multiplier on receptor quantity. |

**Verification (done, no study launched):** all three scripts byte-compile; the sim's parser
is conflict-free (`-STDP` is not ambiguous with `-STDP_A_*`); and the exact argument vector
the harness builds parses to the right typed values. The sim was also run end-to-end (the
bit-identical checks above). I did **not** run the study — not even a sanity trial.

## Launch commands (you run these; I did not)

```bash
source ~/BrainGenix/BrainEmulationChallenge/venv/bin/activate
cd ~/BrainGenix/BrainEmulationChallenge/src/models/autoassociative

# Sanity run first: 5 trials, ~1 minute. Confirms the harness drives sims and
# writes optuna_results/autoassociative.db. (Study is resumable, so these 5
# trials also count toward the full run below — same -StudyName.)
python optuna_autoassociative.py -Host localhost -Port 8000 -Trials 5

# Full run: 100 trials, ~20 minutes (sequential, ~12 s/trial; scales linearly,
# e.g. 200 trials ~40 min). Resumes the same SQLite study.
python optuna_autoassociative.py -Host localhost -Port 8000 -Trials 100
```

Estimated time: **~12 s/trial → 100 trials ≈ 20 min, 200 ≈ 40 min.** Given that budget,
100–200 trials is comfortable in a short wall-clock window; I set the default to 100.

Per repo policy I did not auto-pick a winner — the study reports `best_trial`; you decide.

## Environment (running now; may be stale when you return)
- Stack is three tiers: `client (-Port 8000) → BrainGenix-API :8000 → BrainGenix-NES :8001`.
- tmux `nes` → NES on :8001; tmux `api` → API on :8000. A full run completes in ~12 s and
  auth returns in 0.0 s once both are up.
- If either server is down: start NES first (`~/BrainGenix/BrainGenix-NES/Tools/Run.sh`),
  then API (`~/BrainGenix/BrainGenix-API/Tools/Run.sh`), each in its own tmux window. The
  NES process idling at ~230% CPU is its RPC busy-poll baseline, not a stuck sim.
- The 10-minute timeouts from the earlier session were **not** slowness — they were the
  client hung on `POST /Auth/GetToken` when only NES was up and nothing served auth. Resolved
  by running the API tier.

## Flagged but not fixed
- **STDP-off default** (the bug-adjacent item above) — needs Randal's confirmation of intent.
- **`RunAndWait(timeout_s=100.0)`** is hardcoded in the circuit script; harmless at ~8 s sim
  time, left as-is. The optimizer wraps its own 120 s subprocess timeout on top.
- **All-ones training pattern** makes "completion" a weaker test than a mixed pattern would
  (an all-fire state trivially matches the target on the recall bits). The gap-silence control
  compensates by rejecting saturation, but if you want a stronger test later, a non-all-ones
  trained pattern would make completion unfakeable by construction. Out of scope for this pass.

## Artifacts (all in `src/models/autoassociative/`)
- `autoassociative_lifc.py` — parameterized circuit + inline SCORE (Phase 2).
- `optuna_autoassociative.py` — TPE harness (Phase 3).
- `phase1_diagnostic.py` — diagnostic CLI + the shared `score_recall()` scorer.
- `SESSION_STATUS.md` — this file.
- `optuna_results/autoassociative.db` — created on first launch (does not exist yet).

## What I did NOT do
- Did not launch the study — no sanity run, no full run.
- Did not modify `LIFtest.py` (including the STDP flag) — flagged only.
- Did not select a "winning" parameter set.
