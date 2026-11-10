"""Flask UI for Netmorph parameter optimization (single or joint multi-target).

Backed by ../multi_target_optim.py (RandomForest per target + conservative 2.5th-percentile
model + DiCE + biological-realism checks). No quantile_forest dependency any more.

Environment:
  NETMORPH_DATA       labeled xlsx/csv (default: Pyr->Pyr combined file)
  NETMORPH_TARGETS    comma list of target columns (default: all known target columns present)
  NETMORPH_TREES      RF trees (default 500; Phase2 notebook used 2000)
  NETMORPH_SYNTHETIC  "1" -> use SYNTHETIC labels (pipeline testing only; UI shows a banner)
"""
import os
import random
import sys

import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, render_template

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PARENT)
import bio_check  # noqa: E402
import multi_target_optim as mto  # noqa: E402

app = Flask(__name__)
STATE = {"mtm": None}
# Marianna's original UI default for dm.weight was 0.3-0.7; keep it as the UI default.
UI_RANGE_OVERRIDES = {"dm.weight": [0.3, 0.7]}


def init_model(force=False):
    if STATE["mtm"] is not None and not force:
        return STATE["mtm"]
    synthetic = os.environ.get("NETMORPH_SYNTHETIC") == "1"
    data = os.environ.get("NETMORPH_DATA", os.path.join(PARENT, "Phase1_1500_700_combined_labeled-RS20240628.xlsx"))
    if synthetic:
        raw = bio_check.clean_columns(pd.read_excel(os.path.join(PARENT, "ParameterSpace_700_samples-labeled.xlsx")))
        df = mto.make_synthetic_labels(raw)
    else:
        df = bio_check.clean_columns(pd.read_excel(data))
    env_t = os.environ.get("NETMORPH_TARGETS")
    targets = env_t.split(",") if env_t else [t for t in mto.KNOWN_TARGETS if t in df.columns]
    df, features = mto.load_labeled(df, targets)
    print(f"Loading {'SYNTHETIC ' if synthetic else ''}data ({len(df)} rows), targets={targets}, features={features}")
    mtm = mto.MultiTargetModel(targets, features, int(os.environ.get("NETMORPH_TREES", 500)), synthetic=synthetic).fit(df)
    if not mtm.trained:
        raise RuntimeError(f"no target could be trained: {mtm.report()}")
    STATE["mtm"] = mtm
    return mtm


def _default_thresholds(t):
    return {"min": 500.0, "max": 2500.0} if t == "usable_conns2" else {"min": 300.0, "max": None}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/config")
def config():
    mtm = init_model()
    return jsonify({"features": mtm.features, "synthetic": mtm.synthetic, "report": mtm.report(),
                    "trained_targets": mtm.trained, "target_labels": mto.KNOWN_TARGETS})


@app.route("/api/default_values", methods=["GET"])
def get_default_values():
    mtm = init_model()
    first = mtm.models[mtm.trained[0]]
    Xte = first.X_test[mtm.features]
    inst = Xte.iloc[random.randint(0, len(Xte) - 1)].to_dict()
    pr = {**mto.default_permitted_ranges(mtm.features), **UI_RANGE_OVERRIDES}
    pr = {k: v for k, v in pr.items() if k in mtm.features}
    q = first.pi(pd.DataFrame([inst]))[0]
    t0 = _default_thresholds(first.target)
    return jsonify({
        "query_instance": inst,
        "prediction": {"median": float(q[1]), "lower": float(q[0])},
        "permitted_ranges": pr,
        "desired_range": [t0["min"], t0["max"] or 2500.0],
        "threshold": t0["min"],
        "features_to_vary": mtm.features,
        "features": mtm.features,
        "synthetic": mtm.synthetic,
        "targets": [{"name": t, "label": mto.KNOWN_TARGETS.get(t, t), "trained": t in mtm.trained,
                     "test_r2": mtm.models[t].metrics.get("test_r2"),
                     "n_rows": mtm.models[t].metrics.get("n_rows"),
                     "default": _default_thresholds(t), "selected": t == mtm.trained[0]}
                    for t in mtm.targets],
    })


@app.route("/api/generate", methods=["POST"])
def generate():
    mtm = init_model()
    data = request.get_json(force=True)
    try:
        if data.get("targets"):          # multi-target payload: {"targets": {name: {min, max}}}
            thresholds = {}
            for t, th in data["targets"].items():
                if t not in mtm.trained:
                    return jsonify({"success": False, "error": f"target '{t}' has no trained model "
                                    f"(too few labeled rows): {mtm.models.get(t).metrics if t in mtm.models else 'unknown'}"}), 400
                mx = th.get("max")
                thresholds[t] = {"min": float(th["min"]), "max": None if mx in (None, "") else float(mx)}
        else:                            # legacy single-target payload (Pyr->Pyr)
            dr = data.get("desired_range", [500.0, 2500.0])
            first = "usable_conns2" if "usable_conns2" in mtm.trained else mtm.trained[0]
            thresholds = {first: {"min": float(dr[0]), "max": float(dr[1])}}
        feats = mtm.features
        query = {f: float(data["query_instance"][f]) for f in feats}
        permitted = {k: [float(v[0]), float(v[1])] for k, v in (data.get("permitted_range") or {}).items() if k in feats}
        cfs = mto.generate_joint_cfs(mtm, thresholds, query=query, total_CFs=int(data.get("total_CFs", 7)),
                                     permitted_range=permitted, features_to_vary=data.get("features_to_vary") or feats)
        first_t = next(iter(thresholds))
        q = mtm.models[first_t].pi(pd.DataFrame([query]))[0]
        recs = []
        for _, r in cfs.iterrows():
            d = {k: (v.item() if hasattr(v, "item") else v) for k, v in r.to_dict().items()}
            d["pred_median"], d["pred_lower"] = d[f"{first_t}__pred_median"], d[f"{first_t}__pred_lower"]  # legacy keys
            recs.append(d)
        return jsonify({"success": True, "synthetic": mtm.synthetic, "targets": list(thresholds),
                        "thresholds": thresholds, "features": feats,
                        "query_predictions": {"median": float(q[1]), "lower": float(q[0])},
                        "counterfactuals": recs})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    init_model()
    app.run(host="0.0.0.0", port=5001, debug=True)
