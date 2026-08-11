#!/usr/bin/env python3
# optuna_usable_connections.py
# TPE study tuning NETMORPH growth parameters to maximize the density of
# FUNCTIONALLY USABLE pyramidal-pyramidal connections.
#
# Objective: usable_connections_method2 / pyramidal**2  (maximize).
#
#   method2 (Randal's) counts pre-post pyramidal pairs whose summed AMPA peak
#   conductance reaches PREPOSTGPEAKSUMTARGET -- i.e. pairs strong enough to
#   actually carry retrieval, not merely structurally present (that is method1,
#   Marianna's, which is reported alongside but NOT optimized).
#
#   The raw count is normalized because `pyramidal` is itself a search parameter:
#   without normalization the optimizer wins by growing more neurons rather than
#   better connectivity. The SQUARE is what the data says, not an assumption --
#   method2 counts pre-post PAIRS, and a controlled 5-point sweep (2026-08-10/11,
#   only `pyramidal` varied; days=24, interneuron=48, minneuronseparation=14,
#   shape.radius=120, shape.thickness=30, dm.weight=0.3 held fixed) measured a
#   least-squares log-log slope of ~1.96 over pyramidal 16..64:
#       pyr    16   24   32    48    64     (conns2)
#       conns2 48   81   157   334   717
#   That is much closer to quadratic than linear -- dividing by pyramidal alone
#   would leave the score almost perfectly predicted by population size (gameable);
#   dividing by pyramidal**2 leaves a mild negative residual instead, which is the
#   safer failure mode since it can only bias toward smaller, cheaper populations.
#
# Each trial writes a ONE-ROW parameter sheet with the Optuna-suggested values and
# runs gen_autonm_labels.py against it. Parameters therefore come from the sampler,
# never from the static 700-row sheet; that sheet's observed per-column min/max only
# informed the search bounds below.
#
# Sequential only (single local NES backend on :8001 via the API on :8000; never
# parallelize per repo policy).
#
# COST MODEL (measured 2026-08-10, this machine): growth time is roughly LINEAR in
# `pyramidal` -- 24 pyr -> 235 s, 96 pyr -> 1018 s. Across the 16-128 search range that
# averages ~12 min/trial and reaches ~25 min in the pyramidal=128/days=25 corner. Budget
# from that, NOT from the ~4 min figure an all-low-population sample suggests, and not
# from the LIFC studies in this folder (~12 s/trial).
#
# Usage: python optuna_usable_connections.py -Host localhost -Port 8000 -Trials 8

import argparse
import json
import os
import shutil
import subprocess
import sys
import time

import optuna
import pandas as pds

Parser = argparse.ArgumentParser(description="Optuna tuner for NETMORPH usable connections (method2)")
Parser.add_argument("-Host", default="localhost", type=str)
Parser.add_argument("-Port", default=8000, type=int)
Parser.add_argument("-Trials", default=8, type=int)
# NOTE: study name changed with the objective. `usable_conns2_v1` holds /pyramidal-scored
# trials; mixing the two definitions in one study would average incomparable values.
Parser.add_argument("-StudyName", default="usable_conns2_norm2_v1", type=str)
Parser.add_argument("-TimeoutS", default=1800.0, type=float, help="Per-trial subprocess hard cap (def: 1800 s)")
Parser.add_argument("-MaxMinutes", default=0.0, type=float, help="Wall-clock budget: stop starting NEW trials after this many minutes (def: 0, no limit)")
Parser.add_argument("-RandomSeed", default=20240628, type=int, help="NETMORPH seed, held FIXED across trials (def: 20240628)")
Parser.add_argument("-SamplerSeed", default=0, type=int, help="TPE sampler seed; ADVANCED by the resumed trial count so a restart does not replay (def: 0)")
Parser.add_argument("-KeepTrialDirs", action="store_true", help="Keep per-trial working dirs (def: delete on success)")
Args = Parser.parse_args()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GEN_SCRIPT = os.path.join(SCRIPT_DIR, "gen_autonm_labels.py")
MODEL_FILE = os.path.join(SCRIPT_DIR, "nesvbp-autoassociative")
DB_DIR = os.path.join(SCRIPT_DIR, "optuna_results")
TRIALS_DIR = os.path.join(DB_DIR, "usable_conns_trials")
os.makedirs(TRIALS_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "usable_connections.db")

SIM_RETRIES = 2          # NETMORPH growth is ~4 min; a 3rd attempt costs more than it's worth
RETRY_BACKOFF_S = 10.0

# Column order is irrelevant to gen_autonm_labels.py (it looks columns up by name),
# but kept in the sheet's order for readability when inspecting a trial dir.
PARAM_COLUMNS = ["days", "pyramidal", "interneuron", "minneuronseparation",
                 "shape.radius", "shape.thickness", "dm.weight"]


class SimCommsError(RuntimeError):
    pass


def run_sample(params, trial_number):
    """Grow one NETMORPH sample at `params`; return (usable_conns2, usable_conns1, seconds).

    Runs in a private working directory because gen_autonm_labels.py and BatchRun
    keep ALL their state in files relative to cwd -- batchinfo_completed.json in
    particular. That file is a resume ledger: prepare_batch_information() skips any
    runID already recorded in it, so a shared cwd would make every trial after the
    first silently skip its growth and re-report trial 0's numbers.

    The result is read from batchinfo_completed.json, not from the exit status:
    gen_autonm_labels.py ends on an interactive input() prompt and so exits 1 with
    EOFError on every successful non-TTY run (SESSION_STATUS_usable_connections.md
    Sec.4). stdin is closed here deliberately -- that turns the prompt into an
    immediate EOF rather than a hang -- and the exit code is ignored.

    A comms failure (method1/method2 returning -1, or no ledger written) is RAISED,
    not scored 0.0: a real "this geometry grows no usable connections" zero must stay
    distinguishable from a dropped request.
    """
    trial_dir = os.path.join(TRIALS_DIR, "trial_%04d" % trial_number)
    shutil.rmtree(trial_dir, ignore_errors=True)
    os.makedirs(trial_dir)

    # One-row sheet => numsamples == 1 => exactly one NETMORPH growth per trial.
    sheet_path = os.path.join(trial_dir, "trial_params.xlsx")
    pds.DataFrame([{c: params[c] for c in PARAM_COLUMNS}]).to_excel(sheet_path, index=False)

    cmd = [
        sys.executable, GEN_SCRIPT,
        "-Host", Args.Host, "-Port", str(Args.Port),
        "-excel", sheet_path,
        "-modelfile", MODEL_FILE,
        "-ExpsDB", os.path.join(trial_dir, "ExpsDB.json"),
        "-randomseed", str(Args.RandomSeed),
        "-deleteresident",   # free the server-resident sim after scoring, or they accumulate across trials
    ]

    last_err = ""
    for attempt in range(1, SIM_RETRIES + 1):
        # Wipe the ledger so a retry cannot inherit the previous attempt's verdict.
        for stale in ("batchinfo_completed.json", "batchinfo_completed_backup.json"):
            try:
                os.remove(os.path.join(trial_dir, stale))
            except FileNotFoundError:
                pass

        t0 = time.time()
        try:
            result = subprocess.run(cmd, cwd=trial_dir, stdin=subprocess.DEVNULL,
                                    capture_output=True, text=True, timeout=Args.TimeoutS)
            elapsed = time.time() - t0
            with open(os.path.join(trial_dir, "run.log"), "w") as f:
                f.write(result.stdout + "\n===== STDERR =====\n" + result.stderr)

            try:
                with open(os.path.join(trial_dir, "batchinfo_completed.json")) as f:
                    ledger = json.load(f)
                entry = ledger["0"]
            except (OSError, ValueError, KeyError):
                last_err = "no result ledger; stderr tail: %s" % result.stderr[-300:]
            else:
                if entry.get("status") != "completed":
                    last_err = "sample status=%s" % entry.get("status")
                elif entry.get("usable_conns1", -1) < 0 or entry.get("usable_conns2", -1) < 0:
                    last_err = "connectome retrieval failed (usable_conns = -1)"
                else:
                    return int(entry["usable_conns2"]), int(entry["usable_conns1"]), elapsed
        except subprocess.TimeoutExpired:
            # NOT retried. Growth time is a deterministic function of the parameters
            # (dominated by `pyramidal`), so a set too slow to finish once will be too
            # slow again -- a retry just spends the cap a second time for nothing, and
            # each timeout orphans a server-side sim that no client remains to delete.
            raise SimCommsError("growth exceeded the %.0f s cap (pyramidal=%d, days=%d)"
                                % (Args.TimeoutS, params["pyramidal"], params["days"]))

        print("    attempt %d/%d failed: %s" % (attempt, SIM_RETRIES, last_err), flush=True)
        if attempt < SIM_RETRIES:
            time.sleep(RETRY_BACKOFF_S)

    raise SimCommsError("sample failed after %d attempts: %s" % (SIM_RETRIES, last_err))


def objective(trial):
    # Search space. Bounds and step sizes are the 700-row sheet's observed per-column
    # min/max and resolution -- used as a sanity guide for what NETMORPH is known to
    # grow, not as a sampling source. Steps match the resolution the config template
    # can actually express (dm.weight is written with '%.1f', so finer is discarded).
    #   days                [20, 25]      growth duration; longer = more arbor, more contacts
    #   pyramidal           [16, 128] /8  excitatory population -- also the objective's denominator
    #   interneuron         [16, 128] /8  inhibitory population (independent of pyramidal in the sheet)
    #   minneuronseparation [10, 15]      soma packing: closer = shorter paths to reach threshold
    #   shape.radius        [100, 200]/10 growth volume radius (um)
    #   shape.thickness     [20, 50] /10  growth volume thickness (um); with radius sets density
    #   dm.weight           [0.1, 1.0]/0.1 axon direction-model weight, steers arbor toward targets
    params = {
        "days":                trial.suggest_int("days", 20, 25),
        "pyramidal":           trial.suggest_int("pyramidal", 16, 128, step=8),
        "interneuron":         trial.suggest_int("interneuron", 16, 128, step=8),
        "minneuronseparation": trial.suggest_int("minneuronseparation", 10, 15),
        "shape.radius":        trial.suggest_int("shape.radius", 100, 200, step=10),
        "shape.thickness":     trial.suggest_int("shape.thickness", 20, 50, step=10),
        "dm.weight":           trial.suggest_float("dm.weight", 0.1, 1.0, step=0.1),
    }

    # trial.set_user_attr() writes through to storage immediately (unlike the return
    # value), so an "error" attr set here survives even though the trial ultimately
    # gets marked FAIL by study.optimize's catch= -- without this, a failed trial's
    # only diagnostic is run.log in a trial dir that -KeepTrialDirs-less runs never
    # clean up on failure (see _cb) but that nothing links back to the DB record.
    try:
        conns2, conns1, elapsed = run_sample(params, trial.number)
    except SimCommsError as e:
        trial.set_user_attr("error", str(e))
        raise

    # Raw values are recorded so any future renormalization is a recompute from the
    # stored study rather than a regrow -- that is how the /pyramidal -> /pyramidal**2
    # switch was made without spending another minute of NETMORPH time.
    trial.set_user_attr("usable_conns2", conns2)
    trial.set_user_attr("usable_conns1", conns1)
    trial.set_user_attr("pyramidal", params["pyramidal"])
    trial.set_user_attr("seconds", round(elapsed, 1))

    return conns2 / float(params["pyramidal"]) ** 2


optuna.logging.set_verbosity(optuna.logging.WARNING)

study = optuna.create_study(
    direction="maximize",
    storage="sqlite:///%s" % DB_PATH,
    study_name=Args.StudyName,
    load_if_exists=True,
)

# The sampler's RNG is seeded at construction and, during TPE's random startup phase, does
# NOT consult trial history -- so a FIXED seed makes every restart of a resumable study
# replay the same parameter sequence from the top. That is not reproducibility, it is a
# treadmill: it cost one full 17-min regrow of an identical point before it was caught.
# Advancing the seed by the resumed trial count keeps a given resume point deterministic
# while guaranteeing a restart explores new ground. NETMORPH's own seed (-RandomSeed) is
# what governs simulation reproducibility, and that stays fixed.
study.sampler = optuna.samplers.TPESampler(seed=Args.SamplerSeed + len(study.trials))

print("Running %d trials (sequential, ~12 min each on average -> ~%.1f h; cap %.0f s/trial) -> %s"
      % (Args.Trials, Args.Trials * 12 / 60.0, Args.TimeoutS, DB_PATH), flush=True)


def _cb(study, trial):
    if trial.state != optuna.trial.TrialState.COMPLETE:
        print("  trial %3d  %s (dropped)" % (trial.number, trial.state.name), flush=True)
        return
    print("  trial %3d  score=%.5f  conns2=%d  conns1=%d  pyr=%d  %.0fs  | %s"
          % (trial.number, trial.value, trial.user_attrs["usable_conns2"],
             trial.user_attrs["usable_conns1"], trial.user_attrs["pyramidal"],
             trial.user_attrs["seconds"],
             "  ".join("%s=%g" % (k, v) for k, v in trial.params.items())), flush=True)
    if not Args.KeepTrialDirs:
        shutil.rmtree(os.path.join(TRIALS_DIR, "trial_%04d" % trial.number), ignore_errors=True)


# catch=SimCommsError: a comms-failed trial is marked FAIL and the study continues,
# rather than aborting the run or poisoning the search with a fake zero.
# timeout= stops Optuna STARTING new trials past the budget; a trial already running is
# allowed to finish, so worst-case overshoot is one trial (<= TimeoutS). Trials already in
# the SQLite study are kept -- the budget applies to this invocation, not the study.
study.optimize(objective, n_trials=Args.Trials, callbacks=[_cb], catch=(SimCommsError,),
               timeout=(Args.MaxMinutes * 60.0 if Args.MaxMinutes > 0 else None))

completed = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
if completed:
    secs = [t.user_attrs["seconds"] for t in completed]
    print("\n%d/%d trials completed.  per-trial seconds: min %.0f  median %.0f  max %.0f  total %.1f min"
          % (len(completed), len(study.trials), min(secs), sorted(secs)[len(secs) // 2],
             max(secs), sum(secs) / 60.0))
    print("Best trial #%d  score=%.5f  (usable_conns2=%d / pyramidal=%d^2)"
          % (study.best_trial.number, study.best_trial.value,
             study.best_trial.user_attrs["usable_conns2"],
             study.best_trial.user_attrs["pyramidal"]))
    print("Best params:")
    for k, v in study.best_trial.params.items():
        print("  %s = %s" % (k, v))
else:
    print("\nNo trials completed.")
