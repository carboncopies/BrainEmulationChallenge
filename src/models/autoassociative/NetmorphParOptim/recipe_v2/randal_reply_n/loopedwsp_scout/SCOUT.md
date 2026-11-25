# LoopedWSP scout: what carries over to our hand-programmed spiking CA3 (2026-11-24)

Research only. No sim, no NES/API call, no emails/git/pushes. The repo was cloned into its own new directory (`repo/LoopedWSP`, shallow clone), the page saved to `page/index.html` (text in `page/page.txt`). I did **not run** their code. The only thing I executed on their files was a `python3 -I` read of the `.npz` weight files (numpy, `allow_pickle=False`) to count entries.

## Sources and status
| item | URL / path | status |
|---|---|---|
| Blog post (23 Nov 2026, MBZUAI authors + "Claude Opus 5.5") | https://mbzuai-oryx.github.io/LoopedWSP/ | FETCHED (curl, full text read; 331 kB HTML). It is a blog post, not a paper; no arXiv or peer review found. |
| Repo | https://github.com/mbzuai-oryx/LoopedWSP | CLONED, READ (README, weights/README, run.py, runner/README, prompts/README, prompts 13, network json/npz sizes) |
| Weight-Space Programming (Takehi, Teoh, Zhang, Khattab) | search results only (DataCamp, Register, arXiv 2611.08070 / 2611.09382 / 2611.16981 listed) | UNVERIFIED: not fetched; reported by secondary coverage as a personal blog post, unreviewed, one LLM, networks <= 0.8B |
| NEF / Eliasmith spiking attractors | https://compneuro.uwaterloo.ca/files/publications/eliasmith.2005b.pdf (search result, not opened) | UNVERIFIED (title/snippet only) |
| Formation and retrieval of cell assemblies in a realistic CA3 model | https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10996657/ (search result) | UNVERIFIED (snippet only; learned, not constructed) |
| Frady and Sommer, spiking from phase-to-timing mapping | https://redwood.berkeley.edu/wp-content/uploads/2020/08/frady-sommer-tpam.pdf (search result) | UNVERIFIED (snippet only) |

## 1. What is verified in the repo, and what is blog claim
**Verified by reading files (VERIFIED, repo):**
- The repo holds final weights (`.npz` + `.json`) for 10 networks in `weights/networks/` and more in `weights/more_networks/`, a generic runner (`run.py`, `runner/looped.py`), per-task tokenizers and the first message of each experiment (`prompts/`). The runner is a plain loop: embed, then R times (attention + ReLU MLP, shared block), then a linear readout. Python only maps text to ids and back.
- The maze network has d_model 35, 4 heads of dim 8, `loops = 2 x number of tokens` (maze.json). That agrees with the blog text (35 numbers per cell, 4 direction heads, 2n loops).
- **Weight counting is inconsistent (VERIFIED by counting the npz):** `maze.npz` has 19,936 array entries but only **922 nonzero**; `maze_size_1k` has 928 entries but only **136 nonzero**; `hanoi.npz` has 427,654 entries and **3,686 nonzero**. So "19,936 weights" and "928 weights" count zeros (prompt 13 says "every entry of every array ... zeros included"), while the blog's "3,686 weights" for Hanoi is the nonzero count. The headline "1,900x fewer than LDT" depends on counting zeros; counted by nonzero entries the numbers are far smaller (maze 922, the 1k build 136). This is not an error in their arithmetic, but it is not one consistent unit.
- The prompts show the rules each builder got: DEV/TEST split, TEST run once, no gradient fitting, an enforced DEV-run budget (20 runs, a ledger written by a tool the builder must not edit), a checked transcript, "STOP and report back before running TEST", report every run, report total and nonzero weights.

**NOT in the repo (so UNVERIFIED by me):**
- The weight-writing scripts (`write_weights.py`), the fixed-point test, the DEV/TEST harness, the ledger, the auditor and the build logs are **not** in the repo (only referenced by the prompts). Nobody outside the authors can re-derive the weights, check the "39 minutes / $19" cost, or inspect the audit.
- All headline numbers (100% on Maze-Hard, 100% on 141,040 Sudoku puzzles, 0% for trained-from-random, 0% for 185 + 111 checkpoints, "26% / 38% for Claude alone") are blog claims. They could be re-checked by running `weights/run.py` (numpy, ~30 s per 30x30 maze), which I was told not to do.
- "Claude authored it" rests on the transcript statement; I cannot check it. Claude Opus 5.5 is a listed author.

**Critical points on the claims:**
- The setup is a task with a known exact algorithm (BFS, Hanoi recursion, Sudoku search) and a discrete state snapped to 0/1 after every loop. Correctness is argued by induction over loops (appendix B), not tested with noise. It has **no biological limits, no noise, no timing, no inhibition, no rates**. Transformers are synchronous and non-spiking, so no guarantee transfers.
- "Gradient descent did not find these weights" is shown for one architecture, 1,000 mazes, one training recipe family; it says nothing about what a better recipe would do.
- Fair points: the fixed-point/"extra loops don't undo" property is a real design property (not a measurement); the "blind reading" test (3 fresh sessions recovered the design 11/11 from weights alone) is an interesting audit method but is a blog claim.

## 2. The five candidate techniques: verdicts
Our current failures: (R) reverberation of dense learned assemblies, 200-440 ms at ~65 Hz, not stopped by GABA x1/x2 (partial_cue Addendum B/C); (C) capacity of about 2 hand-designed memories, or 1 dense assembly, per grown network (fresh_learn, math_run, lp_weights).

### (1) Per-weight meaning table + exact-spec audit of programmed weights. SURVIVES (hygiene, not a fix)
- **What they do:** the builder decides what every state variable means before writing any weight; an audit then checks the weights against that spec (and 3 blind sessions rebuilt the meaning from the weights).
- **Maps to:** `lp_weights/`, `math_run/`, `ovlib.pair_list_ov`, `pwlib.arm_matrix`, the read-back asserts in `run_pc.py`/`run_pl.py`.
- **Concrete step:** a "role table" per programmed pair (cue->non-cue, loop, background, hub-capped, member) written with the weights, and an offline `audit.py` that reads back from NES (`read_conn`) and checks the biology rules (per-pair <= 6.86 nS, w in [0.1, 1.0], NMDA r <= 1.0, GABA x1-x2, input cap, hub flags) plus "intended pairs == read-back pairs". We already do much of this per run; the new part is a standing audit file and a blind-read check (give a fresh reader only the read-back matrix and the recipe, ask it to recover the memories).
- **Effect on failures:** none on R or C directly. It would have caught several of our own surprises earlier (NMDA cap at the grown 0.55 nS/synapse achieving r 0.5-0.6 instead of 0.56/1.0; hubs over the 49.5 nS cap).
- **Biological risk:** none. **Sim cost:** 0 (offline) plus the existing read-back.

### (2) One shared circuit looped across cycles (theta-like cue->complete->silence). SURVIVES ONLY AS A CLOCK, NOT AS CAPACITY
- **What they do:** one block repeats one step; more passes, not more weights; a clean state is re-read each pass. Their capacity gain is "problem size per weight", not "number of stored items per weight".
- **What does not transfer:** looping does not add memories. Our capacity limit is the number of dense, mutually completing assemblies that fit the grown graph (fresh_learn: median 0-1), which a time loop does not change. Reading several memories one after another from one circuit still needs them stored in the weights.
- **What could transfer (R):** a **periodic reset**. Their loop clean-up is a forced return to a defined state each pass. The biological version is rhythmic inhibition at theta (septal/interneuron drive), so completion must finish inside one excitatory phase and the inhibitory phase forces silence even if the assembly would reverberate.
- **Concrete NES step:** a periodic drive on the interneuron group (spike-train/current input to Int cells every 125-200 ms, e.g. 8 Hz, duty fixed in advance), applied with `SetSpecificAPTimes`/current injection on the Int cells; check whether the LH/W70 arms' 200-440 ms events are cut at the next inhibitory phase and whether completion from 50-75% cues survives in the excitatory phase. Cue timed to the excitatory phase. Check the existing idea_scout3 entries for septal/theta rhythm before spending (I did not find a separate theta item in the headings I skimmed; verify).
- **Expected effect:** truncates reverberation to <= one half-cycle (~60-100 ms) rather than preventing it; does nothing for capacity. May lower completion if the inhibitory phase arrives too early.
- **Biological risk:** medium: medial-septal rhythmic input to hippocampal interneurons exists (from memory, UNVERIFIED here), but an externally imposed clock is a stronger assumption than a mechanism that is intrinsic to the assembly; must be labelled as imposed. **Sim cost:** about 6 (2 models x 3 conditions) plus 1 reserve slot for a failed load.

### (3) Persistent per-cell state across passes (adaptive threshold / slow AHP). SURVIVES; already in our queue as idea_scout3 #2
- **What they do:** each token keeps a vector of state across loops (for Sudoku, whole saved grids); state variables are monotone where possible ("visited" flags that never revert), so the process ends in a fixed point.
- **Maps to:** the sAHP / adaptive-threshold knobs (idea_scout3 idea 2; NES neuron fields for sAHP gmax and decay). A strong, slow per-cell adaptation is exactly a "visited" flag: a cell that fired cannot fire again for the rest of the event, so a completion wave terminates by construction.
- **New from this source:** the framing "make the end state monotone": choose sAHP so that each member fires about 1-3 spikes in an event and then stays silent for >= 500 ms (about the time the dense arms reverberate), instead of tuning pair strengths in a narrow band (Addendum C found 0.5-0.7 of ceiling, model dependent).
- **Expected effect on R:** large if the adaptation is strong enough; the cost is recovery history: the next cue within seconds sees raised thresholds (we already need 3 s spacing; the sAHP time scale is 1.5 s with tail 3-20 s, UNVERIFIED for CA3 in idea_scout3). **Biological risk:** low to medium (time constants measured, CA3 conductance unverified). **Sim cost:** about 6 (as in idea_scout3), 2 more if combined with the reset idea.

### (4) Treating the finished state as stable (silence-after-completion as a fixed point). SURVIVES ONLY AS AN ANALYSIS, THE GUARANTEE DOES NOT TRANSFER
- **What they do:** after the last pass, a further pass leaves every number unchanged (proved by induction and snapping to clean 0/1). They also show the contrast with trained looped models that "overthink".
- **Why it does not transfer as a guarantee:** a dense assembly that completes from 50-75% cues must have members whose input from the other members exceeds threshold, which is also the condition for a self-sustaining ignited state. Completion and silence conflict in a purely excitatory threshold network (this is the window problem of fresh_learn and the 200-440 ms events). A transformer avoids it because state is discrete and snapped each pass; a spiking network needs an explicit terminating mechanism (adaptation, inhibition, rhythmic drive).
- **What is useful (offline, 0 sims):** state the target as a fixed-point condition and check it before simming: for each candidate assembly, (a) the completed state must lie in a transient, not an attractor, of the model including the adaptation and inhibition we add, (b) a linear-stability check of the "all members on" state with the added terms. Use this to choose parameters for ideas (2) and (3) instead of a blind sweep, and to explain W70 vs W50 (model dependent) before more sims. The threshold model without adaptation under-predicts (W70: 1/6 vs 5/6), so use a rate/Vm model with adaptation, not the bare threshold one.
- **Biological risk:** none (analysis). **Sim cost:** 0.

### (5) LLM writes and verifies the weights; tests, failure handling, minimal 928-weight version. PARTLY; process survives, the claim does not
- **Process worth copying (VERIFIED from prompts):** hard DEV/TEST separation; an enforced run budget with a ledger the builder cannot edit; an independent auditor that checks the transcript and the ledger; "stop and report before the final run"; report every run; report weights total and nonzero; a minimal-size cap that makes a fresh builder prune. Our preregistration/DEVIATIONS and sim cap already do most of this; the ledger (a tool-enforced count of sims, including failed loads) is the missing piece: our 50-sim cap was kept by hand and a failed load almost broke it.
- **Minimal version:** the "928 weights" has 136 nonzero entries and is a size cap on a discrete algorithm; the analogue for us is a **minimal set of programmed pairs**: ask for the sparsest synapse set (L1 objective over pairs, keeping the 6.86 nS per-pair and 49.5 nS input caps) that still gives completion in the threshold model. `thin.py`/`thin_*.json` in randal_reply_n already prune; lp_weights has the LP. A sparser design lowers hub input and may reduce reverberation. Offline, 0 sims.
- **What does not transfer:** "an LLM can write weights that run 100% correctly" relies on a deterministic exact simulator the builder can test in seconds (their DEV runs). Our simulator takes minutes per sim and is capped at 50, so an LLM-in-the-loop weight search is not possible; offline models are the only fast loop and they mispredict (Addendum C).
- **Biological risk:** none. **Sim cost:** 0.

## 3. Related prior work on constructed (not trained) recurrent or spiking networks
All from search results / snippets only, UNVERIFIED unless noted; none was read in full.
- **Neural Engineering Framework / Nengo (Eliasmith and Anderson 2003; Eliasmith 2005 "Unified approach to building and controlling spiking attractor networks"):** weights for spiking integrators and attractors derived analytically from a dynamical-systems specification, no learning. https://compneuro.uwaterloo.ca/files/publications/eliasmith.2005b.pdf. The closest in spirit to "write the weights from a spec"; its controlled attractors (working memory) bear on silence/ignition control. Hand-built, but rate-coded populations, not our graded-pair dense assembly on a grown connectome.
- **Analytic Hopfield/pattern-completion weights:** a patent snippet notes earlier works set synaptic weights deliberately (calculated, not learned) for non-temporal auto-associative pattern completion in spiking recurrent networks. Patent search hit, so weak; treat as a pointer only.
- **Frady and Sommer, TPAM (phase-to-timing mapping):** spiking network built from a phase coding of a Hopfield-type model. https://redwood.berkeley.edu/wp-content/uploads/2020/08/frady-sommer-tpam.pdf. UNVERIFIED snippet.
- **Realistic CA3 assembly model (PMC10996657, 2024):** theta-gamma structure (gamma cycle 20 ms inside a 200 ms theta cycle), partial-cue retrieval, but the weights are learned. Useful as the closest CA3 analogue for the theta idea (2).
- **Transformers:** Tracr / RASP compilers, ALTA, Back de Luca and Fountoulakis (hand-built looped BFS/DFS/Dijkstra), Chiang and Cholak (parity), Giannou et al. (looped transformers as computers): listed in the blog's own related-work appendix I (read in the page); not opened by me. Weight-Space Programming itself: not fetched (see table).
- **Gap:** I found no source that compiles an algorithm into **biologically bounded** (per-synapse cap, input cap, Dale) spiking weights on a grown morphology-based connectome. The search was two searches, not exhaustive.

## 4. Ranked short list
1. **Offline fixed-point / stability analysis of the completed state with adaptation and inhibition (idea 4), 0 sims.** Highest value per cost: tells us before any sim which sAHP strength and pair factor give a transient rather than an attractor, and why W70 works on s77777 but not on s66666.
2. **Monotone per-cell state: strong slow AHP as a "visited" flag (idea 3 = idea_scout3 #2), about 6 sims.** Most direct attack on reverberation, biologically defensible; needs John's approval for sims (50-sim cap is used up).
3. **Theta-phase inhibitory reset as the clock (idea 2), about 6 sims.** Truncates events but imposes a clock; label as imposed; after idea 3 if that fails.
4. **Pair-role table + standing audit + a tool-enforced sim ledger (ideas 1 and 5 process), 0 sims.** Hygiene; stops cap and limit slips.
5. **Sparsest-pairs design under the same caps (idea 5, minimal version), 0 sims.** Low expected gain on R, cheap to try in the offline model.
Not recommended: using looping to claim more memories (capacity gain does not transfer), or LLM-in-the-loop weight search against the simulator (too slow, too few sims).

## 5. Caveats
- Blog numbers are the authors' claims; the repo lacks the builder code, tests and audit, so "LLM wrote it, no training" cannot be checked from the repo.
- I did not run their runner; "100%" is unreproduced by me.
- Related-work items for spiking networks come from 3 search calls and snippets, not opened papers.
- All mappings to our NES knobs are my inferences from our own files (partial_cue README, idea_scout3/IDEAS.md headings, lp_weights, math_run), not from their work.
