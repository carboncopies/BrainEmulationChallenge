#!/usr/bin/env python3
"""
Black-box substitute (SUB) generator for XOR in-domain evaluation.

Uses the vendored IF XOR stack in ``vendor_if_xor`` (no IFneuron-model repo).

Runs ``run_single_in_domain_trial`` on the same schedule as NES acquisition
(``trial_map.json``): within each 100 ms trial, active inputs at t_in_trial = 0 ms.

Input alignment: IF ``Neuron_A`` / ``Neuron_B`` → ``PyrIn_A``, ``PyrIn_B1`` & ``PyrIn_B2``
(duplicate B). ``Neuron_E`` → ``E``.

Writes CSVs compatible with ``build_h5.py`` (column schema matches NES exports).
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Tuple

from vendor_if_xor import run_single_in_domain_trial


def _normalize_case(case: str) -> str:
    s = str(case).strip()
    if s.upper().startswith("XOR_"):
        return s.split("_", 1)[-1]
    return s


def _pattern_to_bits(pat: str) -> Tuple[int, int]:
    pat = pat.zfill(2)[-2:]
    if len(pat) != 2 or not all(c in "01" for c in pat):
        raise ValueError(f"Invalid XOR pattern case: {pat!r}")
    return int(pat[0]), int(pat[1])


def _load_neuron_ids(net: Dict[str, Any]) -> Dict[str, int]:
    neurons = net["neurons"]
    return {str(meta["label"]): int(nid) for nid, meta in neurons.items()}


def run(args: argparse.Namespace) -> None:
    trial_path = Path(args.trial_map).resolve()
    net_path = Path(args.network_config).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    vm_name = Path(args.vm_csv).name
    spike_name = Path(args.spikes_csv).name

    with trial_path.open() as f:
        trial_map: List[Dict[str, Any]] = json.load(f)
    with net_path.open() as f:
        net_cfg = json.load(f)

    labels_to_id = _load_neuron_ids(net_cfg)
    need = ("PyrIn_A", "PyrIn_B1", "PyrIn_B2", "E")
    for k in need:
        if k not in labels_to_id:
            raise KeyError(f"network_config missing label {k!r}; have: {sorted(labels_to_id)}")

    id_pyr_a = labels_to_id["PyrIn_A"]
    id_pyr_b1 = labels_to_id["PyrIn_B1"]
    id_pyr_b2 = labels_to_id["PyrIn_B2"]
    id_e = labels_to_id["E"]

    trial_df = sorted(trial_map, key=lambda r: float(r["t_start"]))
    t_end_max = int(float(trial_df[-1]["t_end"]))
    trial_len = int(float(trial_df[0]["t_end"]) - float(trial_df[0]["t_start"]))
    if any(int(float(r["t_end"]) - float(r["t_start"])) != trial_len for r in trial_df):
        raise ValueError("All trials must have the same length (expected 100 ms blocks).")

    n_neurons = len(net_cfg["neurons"])
    ids_all = sorted(int(k) for k in net_cfg["neurons"].keys())

    vm_global: Dict[int, List[float]] = {nid: [-60.0] * t_end_max for nid in ids_all}
    spikes_rows: List[Tuple[int, float]] = []

    def _pad_vm(seq: List[float], n: int) -> List[float]:
        if len(seq) >= n:
            return list(seq[:n])
        return list(seq) + [-60.0] * (n - len(seq))

    for rec in trial_df:
        t0 = int(float(rec["t_start"]))
        t1 = int(float(rec["t_end"]))
        if t1 > t_end_max:
            raise ValueError("trial extends past t_end_max")
        pat = _normalize_case(rec["case"])
        a_bit, b_bit = _pattern_to_bits(pat)
        a_time = 0 if a_bit else None
        b_time = 0 if b_bit else None
        trial_def = {"a_bit": a_bit, "b_bit": b_bit, "a_time": a_time, "b_time": b_time}

        net, _, _, _, _ = run_single_in_domain_trial(trial_def, trial_len)

        vm_a = _pad_vm([float(x) for x in net.get_neuron_membrane_potentials("Neuron_A")], trial_len)
        vm_b = _pad_vm([float(x) for x in net.get_neuron_membrane_potentials("Neuron_B")], trial_len)
        vm_e = _pad_vm([float(x) for x in net.get_neuron_membrane_potentials("Neuron_E")], trial_len)

        for off, k in enumerate(range(t0, t1)):
            vm_global[id_pyr_a][k] = vm_a[off]
            vm_global[id_pyr_b1][k] = vm_b[off]
            vm_global[id_pyr_b2][k] = vm_b[off]
            vm_global[id_e][k] = vm_e[off]

        for nid, times in (
            (id_pyr_a, net.get_neuron_spike_times_ms("Neuron_A")),
            (id_pyr_b1, net.get_neuron_spike_times_ms("Neuron_B")),
            (id_pyr_b2, net.get_neuron_spike_times_ms("Neuron_B")),
            (id_e, net.get_neuron_spike_times_ms("Neuron_E")),
        ):
            for tloc in times:
                if tloc is None:
                    continue
                g = float(t0) + float(tloc)
                if 0.0 <= g < float(t_end_max):
                    spikes_rows.append((int(nid), g))

    vm_csv = out_dir / vm_name
    with vm_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_ms", "neuron_id", "field", "value"])
        for t_ms in range(t_end_max):
            for nid in ids_all:
                w.writerow([t_ms, nid, "Vm_mV", float(vm_global[nid][t_ms])])

    spike_csv = out_dir / spike_name
    spikes_rows.sort(key=lambda x: (x[1], x[0]))
    with spike_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["neuron_id", "spike_time_ms"])
        for nid, t_ms in spikes_rows:
            w.writerow([nid, t_ms])

    shutil.copy2(trial_path, out_dir / "trial_map.json")
    shutil.copy2(net_path, out_dir / "network_config.json")

    print(f"Wrote black-box SUB CSVs under {out_dir}")
    print(f"  {vm_name} ({t_end_max} ms × {n_neurons} neurons)")
    print(f"  {spike_name} ({len(spikes_rows)} spike rows)")
    print("  trial_map.json, network_config.json (copies)")


def main() -> None:
    p = argparse.ArgumentParser(description="IF XOR black-box SUB → build_h5-compatible CSVs")
    p.add_argument("--trial-map", required=True, type=str)
    p.add_argument("--network-config", required=True, type=str)
    p.add_argument("--out-dir", required=True, type=str)
    p.add_argument(
        "--vm-csv",
        default="blackbox_sub-Vm.csv",
        help="Filename for Vm CSV inside --out-dir (default: blackbox_sub-Vm.csv)",
    )
    p.add_argument(
        "--spikes-csv",
        default="blackbox_sub-spikes.csv",
        help="Filename for spikes CSV inside --out-dir (default: blackbox_sub-spikes.csv)",
    )
    run(p.parse_args())


if __name__ == "__main__":
    main()
