"""
Evaluation profiles for GT vs SUB dashboard scoring.

Profiles control category weights, which metrics count toward /100, and default neuron scope.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

IO_NEURONS = ("PyrIn_A", "PyrIn_B1", "PyrIn_B2", "E")

# Metrics grouped by category (subscores 0–10 each).
CATEGORY_METRICS: Dict[str, List[str]] = {
    "behavior": ["behavior"],
    "spiking": [
        "fano_delta",
        "isi_cv_delta",
        "ks",
        "multi_scale_corr",
        "psth_corr",
        "psth_rmse",
        "raster_jaccard",
        "schreiber",
        "vr_distance",
    ],
    "membrane": ["vm_median_corr"],
    "structure": ["granger_jaccard", "xcorr_matrix_corr"],
}

SCORING_PROFILES: Dict[str, Dict[str, Any]] = {
    "blackbox_io": {
        "label": "Black-box (I/O only)",
        "description": (
            "Scores behavior plus mapped inputs/output (PyrIn_A, PyrIn_B1, PyrIn_B2, E). "
            "Interneuron and structure metrics are shown but excluded from the overall score."
        ),
        "category_weights": {
            "behavior": 20.0,
            "spiking": 2.0,
            "membrane": 1.0,
            "structure": 0.0,
        },
        "excluded_metrics": {"granger_jaccard", "xcorr_matrix_corr"},
        "scope_mode": "io",
        "include_structure": False,
    },
    "full_emulation": {
        "label": "Full emulation",
        "description": (
            "Scores all spiking neurons (or your simulated-neurons list below). "
            "Structure and interneuron metrics are included."
        ),
        "category_weights": {
            "behavior": 20.0,
            "spiking": 2.0,
            "membrane": 1.0,
            "structure": 4.0,
        },
        "excluded_metrics": set(),
        "scope_mode": "simulated_or_all",
        "include_structure": True,
    },
}


def list_profile_ids() -> List[str]:
    return list(SCORING_PROFILES.keys())


def get_profile(profile_id: str) -> Dict[str, Any]:
    if profile_id not in SCORING_PROFILES:
        raise KeyError(f"Unknown scoring profile: {profile_id!r}")
    return SCORING_PROFILES[profile_id]


def parse_simulated_neurons(text: Optional[str]) -> List[str]:
    """Parse comma / newline / semicolon separated neuron labels."""
    if not text or not str(text).strip():
        return []
    raw = str(text).replace("\n", ",").replace(";", ",")
    labels = []
    for part in raw.split(","):
        lab = part.strip()
        if not lab:
            continue
        lab = lab.replace("_spike", "").replace("_vm", "")
        labels.append(lab)
    return sorted(set(labels))

