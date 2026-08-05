#!/usr/bin/env python3
# optuna_autoassociative.py
# TPE study tuning the autoassociative LIFC memory for STABLE pattern completion.
#
# Each trial runs autoassociative_lifc.py once (deterministic: fixed seed, fixed
# all-ones train + half cue), parses its SCORE line, and maximizes clean_recall
# -- the fraction of the 50 cycles with full 4/4 recall of the uncued neurons AND
# silence in the undriven "quiet" gaps. The gap-silence control is baked into the
# score (phase1_diagnostic.score_recall), so a saturated all-fire state CANNOT
# game the objective. Baseline (default params) scores 0.56 (28/50); the goal is
# to widen the recall plateau toward all 50 cycles.
#
# Runs autoassociative_lifc.py WITH -STDP: recall requires plasticity (the script's
# STDP-off default produces zero recall -- see SESSION_STATUS.md).
#
# Sequential only (single local NES backend on :8001 via the API on :8000; never
# parallelize per repo policy). ~12 s/trial.
#
# Usage: python optuna_autoassociative.py -Host localhost -Port 8000 -Trials 100

import argparse
import os
import re
import subprocess
import sys
import time

import optuna

Parser = argparse.ArgumentParser(description="Optuna tuner for autoassociative LIFC memory")
Parser.add_argument("-Host", default="localhost", type=str)
Parser.add_argument("-Port", default=8000, type=int)
Parser.add_argument("-Trials", default=100, type=int)
Parser.add_argument("-StudyName", default="autoassociative_v1", type=str)
Args = Parser.parse_args()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_SCRIPT = os.path.join(SCRIPT_DIR, "autoassociative_lifc.py")
DB_DIR = os.path.join(SCRIPT_DIR, "optuna_results")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "autoassociative.db")

SIM_TIMEOUT_S = 120.0   # a full run is ~12 s; this catches a genuine hang
SIM_RETRIES = 3
RETRY_BACKOFF_S = 5.0


class SimCommsError(RuntimeError):
    pass


def run_sim(params):
    """Run one deterministic sim; return clean_recall in [0,1].

    A dropped sim (timeout / no SCORE line) is retried; if it still fails we
    RAISE so the trial is marked FAIL and skipped, rather than returning a false
    0.0 that a real bad-parameter zero is indistinguishable from.
    """
    cmd = [
        sys.executable, SIM_SCRIPT,
        "-Host", Args.Host, "-Port", str(Args.Port),
        "-STDP",
        "-Weight", str(params["Weight"]),
        "-STDP_A_pos", str(params["STDP_A_pos"]),
        "-STDP_A_neg", str(params["STDP_A_neg"]),
        "-STDP_Tau_pos", str(params["STDP_Tau_pos"]),
        "-STDP_Tau_neg", str(params["STDP_Tau_neg"]),
        "-SuperSynapses", str(params["SuperSynapses"]),
    ]
    last_err = ""
    for attempt in range(1, SIM_RETRIES + 1):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=SIM_TIMEOUT_S)
            match = re.search(r"clean_recall=([\d.]+)", result.stdout)
            if match is not None:
                return float(match.group(1))
            last_err = f"no SCORE line; stderr: {result.stderr[-300:]}"
        except subprocess.TimeoutExpired:
            last_err = "timeout"
        print(f"  attempt {attempt}/{SIM_RETRIES} failed: {last_err}", flush=True)
        if attempt < SIM_RETRIES:
            time.sleep(RETRY_BACKOFF_S)
    raise SimCommsError(f"sim failed after {SIM_RETRIES} attempts: {last_err}")


def objective(trial):
    # Search space (defaults, i.e. the original hardcoded values, in [brackets]):
    #   Weight       [0.5]   log range -- primary recurrent gain. Too low => inert
    #                        (no completion, as with the flat default under STDP-off);
    #                        too high => saturation, which the gap control penalizes.
    #   STDP_A_pos   [0.027] Hebbian potentiation rate: sets how fast the attractor
    #                        forms (recall onset) and, if too strong, drives the
    #                        runaway that collapses recall late in the run.
    #   STDP_A_neg   [0.020] depression rate: the A_pos/A_neg balance is the main
    #                        lever on plateau stability vs. collapse.
    #   STDP_Tau_pos [7.0]   / STDP_Tau_neg [7.0] ms -- STDP timing windows, kept in
    #                        the ballpark of AMPA kinetics.
    #   SuperSynapses[4]     integer coupling multiplier on receptor quantity.
    params = {
        "Weight":       trial.suggest_float("Weight", 0.05, 5.0, log=True),
        "STDP_A_pos":   trial.suggest_float("STDP_A_pos", 0.005, 0.15),
        "STDP_A_neg":   trial.suggest_float("STDP_A_neg", 0.005, 0.15),
        "STDP_Tau_pos": trial.suggest_float("STDP_Tau_pos", 2.0, 40.0),
        "STDP_Tau_neg": trial.suggest_float("STDP_Tau_neg", 2.0, 40.0),
        "SuperSynapses": trial.suggest_int("SuperSynapses", 1, 8),
    }
    return run_sim(params)


optuna.logging.set_verbosity(optuna.logging.WARNING)

study = optuna.create_study(
    direction="maximize",
    sampler=optuna.samplers.TPESampler(),
    storage=f"sqlite:///{DB_PATH}",
    study_name=Args.StudyName,
    load_if_exists=True,
)

print(f"Running {Args.Trials} trials (sequential, ~12 s each -> ~{Args.Trials * 12 / 60:.0f} min) "
      f"-> {DB_PATH}", flush=True)


def _cb(study, trial):
    if trial.state != optuna.trial.TrialState.COMPLETE:
        print(f"  trial {trial.number:3d}  {trial.state.name} (dropped)", flush=True)
        return
    print(f"  trial {trial.number:3d}  clean_recall={trial.value:.3f}  "
          + "  ".join(f"{k}={v:.3g}" for k, v in trial.params.items()), flush=True)


# catch=SimCommsError: a comms-failed trial is marked FAIL and the study
# continues, instead of aborting the whole run.
study.optimize(objective, n_trials=Args.Trials, callbacks=[_cb], catch=(SimCommsError,))

print(f"\nBest trial #{study.best_trial.number}  clean_recall={study.best_trial.value:.3f}")
print("Best params:")
for k, v in study.best_trial.params.items():
    print(f"  {k} = {v}")
