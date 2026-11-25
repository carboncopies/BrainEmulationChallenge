# Deviations from PREREGISTRATION_morph2.md

- **N1 (before any growth, tooling).** The first launch of `run_instance.py` on all 9 instances exited at import: openpyxl lives in `cos/netmorph_work/extra`, which the new driver had not put on `sys.path`. I fixed the path and relaunched about 1 minute later. No growth had started.
- **N2 (analysis tooling, after growth).** The first run of `analyze2.py` found no `NETMORPH_DONE` time for 12 of 39 runs and no `NES_SIM_ID` for any run.
  - Cause: the tqdm progress bar writes to the same line, so `re.match` at line start missed the prints. Also, `NES_SIM_ID` is printed before `NETMORPH_OUT`, and the parser overwrote that entry.
  - Fix: switched to `re.search` and merged the dicts. All 39 runs now have growth time from `NETMORPH_DONE` and a NES_SIM_ID.
  - A `CHECK_DONE` fallback (≤ 12 s later) stays in the code but is unused.
  - The data and criteria were not changed.
- **N3 (scoring note, not a change).**
  - Growth times were measured with up to 27 growths running at once (3 per NES) on a shared machine; the load from other users was not controlled. The time-vs-N fit therefore includes contention. The x3 runs shared the machine with fewer other growths for their last 3–4 h, which flatters x3 slightly.
  - Prediction 11 ("exact" reproduction) is scored strictly.
