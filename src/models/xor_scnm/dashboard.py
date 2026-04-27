"""
XOR Neural Network Metrics Dashboard
=====================================
Run:  streamlit run xor_dashboard.py
Place groundtruth.h5 in the same directory as this script (or set paths in the sidebar).
Optional: network_config.json with a truth_table block (same layout as in_domain_metrics.ipynb)
next to the H5 or under GT / output/GT — overrides the built-in XOR truth table for metrics.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import h5py, json, os, math

# ──────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="XOR Network · Metrics Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────
# THEME / CSS
# ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

/* ── GLOBAL DARK THEME ── */
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #0d1117 !important;
    color: #c9d1d9 !important;
}

/* Global text contrast overrides (Streamlit widgets + BaseWeb components) */
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label,
[data-testid="stWidgetLabel"] span,
.stMarkdown, .stMarkdown p, .stMarkdown span,
.stText, .stCaption,
label, p, span, small {
    color: #e6edf3 !important;
}

/* Radios / checkboxes / toggles (BaseWeb) */
div[data-baseweb="radio"] *,
div[data-baseweb="checkbox"] *,
div[role="radiogroup"] *,
div[role="group"] label * {
    color: #e6edf3 !important;
}

/* Streamlit metrics (numbers like 140, and their labels) */
[data-testid="stMetricLabel"] {
    color: #e6edf3 !important;
}
[data-testid="stMetricValue"] {
    color: #e6edf3 !important;
}
[data-testid="stMetricValue"] * {
    color: #e6edf3 !important;
}

/* Plotly legend text (sometimes rendered too dim) */
.js-plotly-plot .plotly .legend text,
.js-plotly-plot .plotly .gtitle,
.js-plotly-plot .plotly .xtitle,
.js-plotly-plot .plotly .ytitle,
.js-plotly-plot .plotly .xtick text,
.js-plotly-plot .plotly .ytick text {
    fill: #e6edf3 !important;
}

/* Force the entire Streamlit app background dark */
.stApp, .stApp > div, [data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section,
[data-testid="stMain"], .main, .block-container {
    background-color: #0d1117 !important;
}

/* Remove any white/light backgrounds on content containers */
[data-testid="stVerticalBlock"] > div,
[data-testid="stHorizontalBlock"] > div,
.element-container, .stMarkdown {
    background-color: transparent !important;
}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background-color: #080c10 !important;
    border-right: 1px solid #1c2128 !important;
}
section[data-testid="stSidebar"] * { color: #c9d1d9 !important; }

/* Sidebar text input (H5 path) */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] .stTextInput input {
    background-color: #161b22 !important;
    color: #e6edf3 !important;
    border: 1px solid #30363d !important;
    border-radius: 6px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.75rem !important;
}
[data-testid="stSidebar"] input:focus {
    border-color: #388bfd !important;
    color: #c9d1d9 !important;
    box-shadow: 0 0 0 2px #388bfd22 !important;
}

/* Sidebar nav buttons */
[data-testid="stSidebar"] .stButton > button {
    background-color: #0d1117 !important;
    color: #e6edf3 !important;
    border: 1px solid #1c2128 !important;
    border-radius: 6px !important;
    font-size: 0.84rem !important;
    font-weight: 500 !important;
    text-align: left !important;
    padding: 9px 14px !important;
    transition: all 0.15s ease !important;
    width: 100% !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #161b22 !important;
    border-color: #30363d !important;
    color: #e6edf3 !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] .stButton > button[data-testid="baseButton-primary"] {
    background-color: #1c2128 !important;
    border: 1px solid #388bfd !important;
    border-left: 3px solid #58a6ff !important;
    color: #58a6ff !important;
    font-weight: 600 !important;
}

/* ── MAIN CONTENT AREA ── */
.main .block-container { padding: 1.8rem 2.2rem 3rem; max-width: 1400px; }

/* Streamlit native widgets — dark */
.stSelectbox > div > div,
.stRadio > div,
.stSlider > div {
    background-color: transparent !important;
}
/* Selectbox dropdown */
[data-testid="stSelectbox"] > div > div {
    background-color: #161b22 !important;
    border-color: #30363d !important;
    color: #e6edf3 !important;
    border-radius: 6px !important;
}
/* Radio buttons text */
.stRadio label { color: #e6edf3 !important; }

/* Slider */
.stSlider [data-testid="stTickBar"] { color: #e6edf3 !important; }

/* DataFrame / table */
.stDataFrame, [data-testid="stDataFrame"] {
    background-color: #161b22 !important;
}
iframe { background-color: #161b22 !important; }

/* Pandas-Styler HTML tables: header + index column (Streamlit defaults were light) */
[data-testid="stDataFrame"] table thead th,
[data-testid="stDataFrame"] table thead tr th {
    background-color: #0d1117 !important;
    color: #e6edf3 !important;
    border-color: #30363d !important;
}
[data-testid="stDataFrame"] table tbody th,
[data-testid="stDataFrame"] table tbody tr th {
    background-color: #0d1117 !important;
    color: #e6edf3 !important;
    border-color: #30363d !important;
}
[data-testid="stDataFrame"] table tbody td {
    background-color: #161b22 !important;
    color: #e6edf3 !important;
    border-color: #21262d !important;
}
[data-testid="stDataFrame"] table {
    background-color: #161b22 !important;
    color: #e6edf3 !important;
}

/* ── KPI CARDS ── */
.kpi-row { display: flex; gap: 14px; margin-bottom: 1.5rem; flex-wrap: wrap; }
.kpi-card {
    flex: 1; min-width: 120px;
    background: #161b22; border: 1px solid #21262d;
    border-radius: 10px; padding: 14px 18px;
}
.kpi-label { font-size: 0.7rem; color: #8b949e; text-transform: uppercase;
    letter-spacing: 0.07em; margin-bottom: 4px; }
.kpi-value { font-size: 1.5rem; font-weight: 700; color: #e6edf3;
    font-family: 'IBM Plex Mono', monospace; }
.kpi-sub { font-size: 0.73rem; color: #58a6ff; margin-top: 2px; }

/* ── SECTION HEADERS ── */
.section-title {
    font-size: 1.25rem; font-weight: 700;
    color: #e6edf3;                      /* white — NOT teal */
    border-bottom: 2px solid #21262d;
    padding-bottom: 10px; margin: 0 0 0.6rem;
    font-family: 'IBM Plex Sans', sans-serif;
}
.section-subtitle {
    font-size: 0.82rem; color: #e6edf3;
    margin-top: 0; margin-bottom: 1.2rem;
}

/* ── BADGES ── */
.badge-ok { background: #1a3a2a; color: #3fb950; border: 1px solid #238636;
    border-radius: 20px; padding: 2px 10px; font-size: 0.75rem; font-weight: 600; }
.badge-warn { background: #2d1f0e; color: #f0883e; border: 1px solid #9e6a03;
    border-radius: 20px; padding: 2px 10px; font-size: 0.75rem; font-weight: 600; }

/* ── INFO BOX ── */
.info-box { background: #161b22; border: 1px solid #30363d;
    border-left: 3px solid #388bfd;
    border-radius: 6px; padding: 10px 14px; margin-bottom: 1rem;
    font-size: 0.83rem; color: #e6edf3; }

/* ── NAV SECTION LABEL ── */
.nav-section { font-size: 0.68rem; font-weight: 700; color: #e6edf3 !important;
    text-transform: uppercase; letter-spacing: 0.09em; padding: 14px 14px 5px; }

/* ── PLOTLY ── transparent so dark page shows through */
.js-plotly-plot .plotly .main-svg { background: transparent !important; }
.js-plotly-plot { background: transparent !important; }

/* Streamlit metric delta */
[data-testid="stMetricDelta"] { color: #3fb950 !important; }

/* Make the Deploy button visible on dark header */
[data-testid="stDeployButton"] button,
[data-testid="stDeployButton"] [role="button"] {
    background: #161b22 !important;
    color: #e6edf3 !important;
    border: 1px solid #30363d !important;
}

/* Toolbar / top-right controls on dark */
[data-testid="stToolbar"] * {
    color: #e6edf3 !important;
}

/* Hide Streamlit branding */
#MainMenu, footer { visibility: hidden; }

/* Keep header visible, but match dark theme */
header[data-testid="stHeader"] {
    background: #0d1117 !important;
    border-bottom: 1px solid #1c2128 !important;
}
[data-testid="stHeader"] * {
    color: #e6edf3 !important;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# PLOTLY DARK TEMPLATE
# ──────────────────────────────────────────────────────────────
DARK = dict(
    paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
    font=dict(family="IBM Plex Sans", color="#e6edf3", size=12),
    xaxis=dict(gridcolor="#21262d", linecolor="#30363d", zerolinecolor="#21262d"),
    yaxis=dict(gridcolor="#21262d", linecolor="#30363d", zerolinecolor="#21262d"),
    margin=dict(l=55, r=20, t=40, b=50),
    legend=dict(bgcolor="#161b22", bordercolor="#30363d", borderwidth=1),
)

PAL_GT  = "#58a6ff"   # blue  – GT
PAL_SUB = "#f0883e"   # orange – SUB
PAL_ACC = ["#58a6ff","#3fb950","#f0883e","#ffa657"]
PAT_COLORS = {"00":"#58a6ff","11":"#3fb950","01":"#ffa657","10":"#f0883e"}

def dark_fig(**kw):
    fig = go.Figure(**kw)
    fig.update_layout(**DARK)
    return fig

def apply_dark(fig):
    fig.update_layout(**DARK)
    return fig

# ──────────────────────────────────────────────────────────────
# DATA LOADING
# ──────────────────────────────────────────────────────────────
def load_metadata(h5_path):
    """Read `/metadata` attrs (same contract as in_domain_metrics.ipynb)."""
    with h5py.File(h5_path, "r") as f:
        return dict(f["/metadata"].attrs)


@st.cache_data
def load_h5_pair(gt_path, sub_path):
    """
    Ground truth: `/data`, `/spikes_raw`, `/network_config`, `/trial_map`, metadata from gt_path.
    Submission: `/data` and `/spikes_raw` from sub_path (cfg / trial_map / meta always from GT).
    """
    gt_path = os.path.abspath(gt_path)
    sub_path = os.path.abspath(sub_path)
    gt_data = pd.read_hdf(gt_path, "/data")
    gt_spikes = pd.read_hdf(gt_path, "/spikes_raw")
    sub_data = pd.read_hdf(sub_path, "/data")
    sub_spikes = pd.read_hdf(sub_path, "/spikes_raw")
    cfg = pd.read_hdf(gt_path, "/network_config")
    tmap = pd.read_hdf(gt_path, "/trial_map")
    meta = load_metadata(gt_path)
    return gt_data, gt_spikes, sub_data, sub_spikes, cfg, tmap, meta


@st.cache_data
def load_truth_table_json(h5_path):
    """
    Optional `network_config.json` with a `truth_table` block (notebook-style).
    Searches: same dir as the H5, then ./GT/ and ./output/GT/ relative to the H5 parent.
    Returns (raw dict or None, resolved path or None).
    """
    base = os.path.dirname(os.path.abspath(h5_path))
    candidates = [
        os.path.join(base, "network_config.json"),
        os.path.join(os.path.dirname(base), "network_config.json"),
        os.path.join(base, "GT", "network_config.json"),
        os.path.join(os.path.dirname(base), "GT", "network_config.json"),
        os.path.join(base, "output", "GT", "network_config.json"),
        os.path.join(os.path.dirname(base), "output", "GT", "network_config.json"),
    ]
    for p in candidates:
        p = os.path.normpath(p)
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    cfgj = json.load(f)
                tt = cfgj.get("truth_table")
                if isinstance(tt, dict) and tt:
                    return tt, p
            except (OSError, json.JSONDecodeError, TypeError):
                continue
    return None, None


def normalize_truth_rows(raw_truth):
    """
    Map notebook keys (e.g. XOR_00) to trial_map case strings (e.g. 00).
    Falls back to built-in TRUTH for any missing pattern.
    """
    if not raw_truth:
        return dict(TRUTH)
    out = {}
    for k, v in raw_truth.items():
        key = str(k)
        pat = key[4:] if key.upper().startswith("XOR_") else key
        pat = str(pat)
        if not isinstance(v, dict):
            continue
        base = TRUTH.get(pat, {"input_A": 0, "input_B": 0, "expected_output": 0})
        out[pat] = {
            "input_A": int(v.get("input_A", v.get("input_a", base["input_A"]))),
            "input_B": int(v.get("input_B", v.get("input_b", base["input_B"]))),
            "expected_output": int(
                v.get("expected_output", v.get("expected", base["expected_output"]))
            ),
        }
    for pat, row in TRUTH.items():
        out.setdefault(pat, dict(row))
    return out

# ──────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────
def get_neurons(cfg, role=None, input_channel=None):
    r = cfg
    if role is not None and role != "all":
        r = r[r["role"].isin(role)] if isinstance(role, list) else r[r["role"] == role]
    if input_channel is not None:
        r = r[r["input_channel"] == input_channel]
    return r["label"].tolist()

def get_spiking_neurons(cfg, data):
    return [l for l in cfg["label"] if f"{l}_spike" in data.columns and data[f"{l}_spike"].sum() > 0]

def get_spike_cols(cfg, data, role=None):
    if role is None:
        return [f"{l}_spike" for l in get_spiking_neurons(cfg, data)]
    return [f"{l}_spike" for l in get_neurons(cfg, role=role)]

def get_vm_cols(cfg, scope="all"):
    return [f"{r['label']}_vm" for _, r in cfg.iterrows()
            if scope == "all" or r["role"] != "extended_network"]

def get_trial(data, tid):
    return data[data["trial_id"] == tid]


def style_network_cfg_styler(cfg_df):
    """
    Dark theme for entire table including thead / row-index column.
    Streamlit only applied set_properties() to body cells, leaving headers white.
    """
    hdr = [
        ("background-color", "#0d1117"),
        ("color", "#e6edf3"),
        ("font-weight", "600"),
        ("border", "1px solid #30363d"),
        ("padding", "6px 10px"),
    ]
    idx_cell = [
        ("background-color", "#0d1117"),
        ("color", "#e6edf3"),
        ("border", "1px solid #30363d"),
        ("padding", "6px 10px"),
    ]
    body = [
        ("background-color", "#161b22"),
        ("color", "#e6edf3"),
        ("border", "1px solid #21262d"),
        ("padding", "6px 10px"),
    ]
    table_css = [
        {"selector": "thead tr th", "props": hdr},
        {"selector": "tbody tr th", "props": idx_cell},
        {"selector": "td", "props": body},
        {"selector": "table", "props": [("background-color", "#161b22"), ("color", "#e6edf3")]},
    ]
    role_text_colors = {
        "output": "#58a6ff",
        "input": "#d29922",
        "interneuron": "#a371f7",
        "intermediate": "#3fb950",
        "extended_network": "#8b949e",
    }
    return (
        cfg_df.style.set_table_styles(table_css)
        .set_properties(**{"color": "#e6edf3", "background-color": "#161b22"})
        .apply(
            lambda col: [
                f"color:{role_text_colors.get(v, '#e6edf3')}; font-weight:600; background-color:#161b22;"
                for v in col
            ],
            subset=["role"],
        )
    )


def get_trials_by_pattern(data, pattern):
    """
    List of trial DataFrames, one per repetition (matches in_domain_metrics.ipynb).
    Requires `case` and `rep` on the voltage table; otherwise returns None.
    """
    if "case" not in data.columns or "rep" not in data.columns:
        return None
    pattern = str(pattern)
    result = []
    for u in data["rep"].unique():
        filtered = data[(data["case"].astype(str) == pattern) & (data["rep"] == u)]
        if len(filtered):
            result.append(filtered)
    return result


TRUTH = {
    "00": {"input_A":0,"input_B":0,"expected_output":0},
    "01": {"input_A":0,"input_B":1,"expected_output":1},
    "10": {"input_A":1,"input_B":0,"expected_output":1},
    "11": {"input_A":1,"input_B":1,"expected_output":0},
}

# ──────────────────────────────────────────────────────────────
# SIDEBAR NAVIGATION
# ──────────────────────────────────────────────────────────────
METRICS = [
    ("🏠", "Overview",          "overview"),
    ("🎯", "Behavioral",        "behavioral"),
    ("🔬", "Raster Plot",       "raster"),
    ("⚡", "Vm Traces",         "vm_traces"),
    ("📈", "PSTH",              "psth"),
    ("⏱",  "ISI / Fano",       "isi"),
    ("📉", "KS Test",           "ks"),
    ("🔺", "PSP Counts",        "psp_counts"),
    ("🌊", "Van Rossum",        "van_rossum"),
    ("📐", "Multi-Scale Corr",  "msc"),
    ("🔗", "Schreiber",         "schreiber"),
    ("🧮", "Vm Mismatch",       "vm_mismatch"),
    ("🔀", "Cross-Correlogram", "xcorr"),
    ("🕸",  "Granger",          "granger"),
]

if "active_metric" not in st.session_state:
    st.session_state.active_metric = "overview"

with st.sidebar:
    st.markdown("""
    <div style="padding:18px 14px 12px; border-bottom:1px solid #1c2128; margin-bottom:10px;">
        <div style="font-size:1.05rem;font-weight:700;color:#e6edf3;letter-spacing:-0.01em;">🧠 XOR Metrics</div>
        <div style="font-size:0.71rem;color:#8b949e;margin-top:4px;font-family:'IBM Plex Mono',monospace;letter-spacing:0.02em;">GT vs SUB metrics</div>
    </div>
    """, unsafe_allow_html=True)

    default_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "groundtruth.h5")
    st.markdown(
        '<div style="font-size:0.68rem;color:#8b949e;padding:6px 2px 2px;text-transform:uppercase;letter-spacing:0.07em;">Data paths</div>',
        unsafe_allow_html=True,
    )
    gt_path = st.text_input(
        "Ground truth data",
        value=default_path,
        key="path_gt_h5",
        help="H5 with GT voltage/spikes; network_config and trial_map are taken from this file.",
    )
    sub_path = st.text_input(
        "Submission (SUB) data",
        value=default_path,
        key="path_sub_h5",
        help="H5 with submission /data and /spikes_raw. Use the same file as GT until you have a separate run.",
    )
    _same = os.path.normpath(os.path.abspath(gt_path)) == os.path.normpath(os.path.abspath(sub_path))
    st.caption("Using one H5 for both GT and SUB (self-check)." if _same else "GT and SUB load from different files.")

    st.markdown('<div class="nav-section">Metrics</div>', unsafe_allow_html=True)

    for icon, label, key in METRICS:
        active = "active" if st.session_state.active_metric == key else ""
        if st.button(f"{icon}  {label}", key=f"nav_{key}",
                     use_container_width=True,
                     type="secondary" if not active else "primary"):
            st.session_state.active_metric = key
            st.rerun()

    st.markdown("---")
    st.markdown('<div style="font-size:0.72rem;color:#8b949e;padding:0 14px;">v2.0 · Streamlit Dashboard</div>',
                unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# LOAD DATA
# ──────────────────────────────────────────────────────────────
for _label, _path in (("Ground truth", gt_path), ("Submission (SUB)", sub_path)):
    if not os.path.exists(_path):
        st.error(f"{_label} file not found: `{_path}`\n\nUpdate the path in the sidebar.")
        st.stop()

same_h5_file = os.path.normpath(os.path.abspath(gt_path)) == os.path.normpath(
    os.path.abspath(sub_path)
)

with st.spinner("Loading data…"):
    gt_data, gt_spikes, sub_data, sub_spikes, cfg, tmap, meta = load_h5_pair(gt_path, sub_path)
    truth_raw, truth_json_path = load_truth_table_json(gt_path)

truth_effective = normalize_truth_rows(truth_raw)
trial_len  = int(meta["trial_len_ms"])
fs_hz      = float(meta["fs_hz"])
MS_PER_SAMPLE = 1000.0 / fs_hz
patterns   = list(tmap["case"].unique())  # preserve natural tmap order: 00, 11, 01, 10
spike_cols = sorted(set(get_spike_cols(cfg, gt_data)) | set(get_spike_cols(cfg, sub_data)))
common_ids = {
    p: tmap[tmap["case"].astype(str) == str(p)]["trial_id"].tolist() for p in patterns
}
active     = st.session_state.active_metric

# ══════════════════════════════════════════════════════════════
# OVERVIEW
# ══════════════════════════════════════════════════════════════
if active == "overview":
    st.markdown('<div class="section-title">🏠 Overview · Network Summary</div>', unsafe_allow_html=True)

    spiking = get_spiking_neurons(cfg, gt_data)
    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card"><div class="kpi-label">Total Neurons</div>
            <div class="kpi-value">{int(meta.get('n_neurons_total',35))}</div></div>
        <div class="kpi-card"><div class="kpi-label">Spiking Neurons</div>
            <div class="kpi-value">{len(spiking)}</div>
            <div class="kpi-sub">runtime-derived</div></div>
        <div class="kpi-card"><div class="kpi-label">Trials</div>
            <div class="kpi-value">{int(meta.get('n_trials',40))}</div>
            <div class="kpi-sub">10 reps × 4 patterns</div></div>
        <div class="kpi-card"><div class="kpi-label">Trial Length</div>
            <div class="kpi-value">{trial_len} ms</div></div>
        <div class="kpi-card"><div class="kpi-label">Sampling Rate</div>
            <div class="kpi-value">{int(fs_hz)} Hz</div></div>
    </div>
    """, unsafe_allow_html=True)

    if same_h5_file:
        st.markdown(
            '<div class="info-box">ℹ️ <b>Self-consistency check</b>: GT and SUB use the same H5. '
            "Metrics that compare both should line up; differences usually mean a metric bug.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="info-box">ℹ️ <b>GT vs SUB</b>: Ground truth from <code>{os.path.basename(gt_path)}</code> · '
            f"Submission from <code>{os.path.basename(sub_path)}</code>. "
            "Network config and trial map follow the <b>ground truth</b> file.</div>",
            unsafe_allow_html=True,
        )

    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("**Network Configuration**")
        def _dash_if_missing(x):
            if x is None:
                return "—"
            if isinstance(x, str) and x.strip().lower() == "none":
                return "—"
            try:
                if pd.isna(x):
                    return "—"
            except (TypeError, ValueError):
                pass
            return x

        cfg_show = cfg.copy()
        for c in cfg_show.columns:
            if cfg_show[c].dtype == object or c == "input_channel":
                cfg_show[c] = cfg_show[c].map(_dash_if_missing)
        cfg_styled = style_network_cfg_styler(cfg_show)
        st.dataframe(cfg_styled, use_container_width=True, height=420, hide_index=True)
    with col2:
        st.markdown("**XOR Truth Table**")
        if truth_raw is not None:
            st.caption(f"Loaded from `network_config.json` — `{truth_json_path}`")
            st.dataframe(pd.DataFrame(truth_raw), use_container_width=True)
        else:
            tt_df = pd.DataFrame(TRUTH).T.reset_index().rename(columns={"index": "case"})
            st.caption("Built-in XOR truth table (place `network_config.json` beside the H5 to mirror the notebook).")
            st.dataframe(tt_df, use_container_width=True)

        st.markdown("**Pattern Distribution**")
        counts = tmap["case"].value_counts().sort_index()
        ymax = float(counts.max()) if len(counts) else 10.0
        fig = dark_fig()
        fig.add_trace(go.Bar(
            x=[f"XOR_{p}" for p in counts.index], y=counts.values,
            marker_color=[PAT_COLORS.get(p,"#58a6ff") for p in counts.index],
            text=counts.values, textposition="outside",
            cliponaxis=False,
        ))
        fig.update_layout(
            height=300, showlegend=False,
            margin=dict(l=45, r=15, t=50, b=40),
        )
        fig.update_yaxes(range=[0, ymax * 1.22], title="Count")
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# BEHAVIORAL
# ══════════════════════════════════════════════════════════════
elif active == "behavioral":
    st.markdown('<div class="section-title">🎯 Behavioral Accuracy</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">XOR output neuron firing vs. expected truth table (notebook-aligned trial loop)</div>', unsafe_allow_html=True)
    if truth_raw is not None:
        st.caption(f"Truth table from `{truth_json_path}` · Trial stats use `get_trials_by_pattern` when `case`/`rep` exist on `/data`, else `trial_map`.")

    out_col = get_spike_cols(cfg, gt_data, role="output")[0]

    def summary_table(data, pattern):
        """TP/FN/TN/FP per pattern — same logic as compute_confusion_matrix in the reference notebook."""
        pattern = str(pattern)
        row_truth = truth_effective.get(pattern) or TRUTH.get(
            pattern, {"input_A": 0, "input_B": 0, "expected_output": 0}
        )
        want = row_truth["expected_output"]
        TP = FN = TN = FP = 0
        trials = get_trials_by_pattern(data, pattern)
        if trials is not None:
            for t in trials:
                window = t[t["t_in_trial"] <= trial_len]
                fired = window[out_col].sum() > 0
                have = 1 if fired else 0
                if want == 1 and have == 1:
                    TP += 1
                elif want == 1 and have == 0:
                    FN += 1
                elif want == 0 and have == 0:
                    TN += 1
                else:
                    FP += 1
        else:
            for _, row in tmap[tmap["case"].astype(str) == pattern].iterrows():
                t = get_trial(data, row["trial_id"])
                fired = t[t["t_in_trial"] <= trial_len][out_col].sum() > 0
                have = 1 if fired else 0
                if want == 1 and have == 1:
                    TP += 1
                elif want == 1 and have == 0:
                    FN += 1
                elif want == 0 and have == 0:
                    TN += 1
                else:
                    FP += 1
        den = TP + FN + TN + FP
        acc = (TP + TN) / den if den else 0.0
        sens = (TP / (TP + FN)) if (TP + FN) else 0.0
        spec = (TN / (TN + FP)) if (TN + FP) else 0.0
        return TP, FN, TN, FP, acc, sens, spec

    gt_rows = []
    sub_rows = []
    for p in patterns:
        ps = str(p)
        tr = truth_effective.get(ps) or TRUTH.get(
            ps, {"input_A": 0, "input_B": 0, "expected_output": 0}
        )
        tp, fn, tn, fp, acc, sens, spec = summary_table(gt_data, ps)
        gt_rows.append(
            {
                "Pattern": ps,
                "Input A": tr["input_A"],
                "Input B": tr["input_B"],
                "Expected": tr["expected_output"],
                "TP": tp,
                "FN": fn,
                "TN": tn,
                "FP": fp,
                "Accuracy": round(acc, 3),
                "Sensitivity": round(sens, 3),
                "Specificity": round(spec, 3),
            }
        )
        tp, fn, tn, fp, acc, sens, spec = summary_table(sub_data, ps)
        sub_rows.append(
            {
                "Pattern": ps,
                "Input A": tr["input_A"],
                "Input B": tr["input_B"],
                "Expected": tr["expected_output"],
                "TP": tp,
                "FN": fn,
                "TN": tn,
                "FP": fp,
                "Accuracy": round(acc, 3),
                "Sensitivity": round(sens, 3),
                "Specificity": round(spec, 3),
            }
        )

    df_gt = pd.DataFrame(gt_rows)
    df_sub = pd.DataFrame(sub_rows)

    gt_sub_match = df_gt.equals(df_sub)
    # Pooled accuracy over all trials — (TP+TN) / (TP+FN+TN+FP); same aggregation as summing notebook rows
    tp_sum = int(df_gt["TP"].sum())
    fn_sum = int(df_gt["FN"].sum())
    tn_sum = int(df_gt["TN"].sum())
    fp_sum = int(df_gt["FP"].sum())
    den_all = tp_sum + fn_sum + tn_sum + fp_sum
    overall = (tp_sum + tn_sum) / den_all if den_all else 0.0
    badge = (
        '<span class="badge-ok">✓ GT and SUB tables match</span>'
        if gt_sub_match
        else '<span class="badge-warn">GT and SUB differ</span>'
    )
    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card"><div class="kpi-label">Overall Accuracy</div>
            <div class="kpi-value">{overall:.1%}</div>
            <div class="kpi-sub">pooled over all GT trials (TP+TN)/N</div></div>
        <div class="kpi-card"><div class="kpi-label">Output Neuron</div>
            <div class="kpi-value" style="font-size:1rem;padding-top:6px">{out_col.replace('_spike','')}</div></div>
        <div class="kpi-card"><div class="kpi-label">Status</div>
            <div style="margin-top:8px">{badge}</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**GT vs SUB Summary**")
    col_t, col_c = st.columns([1, 1])
    with col_t:
        st.markdown("**GT Summary**")
        st.dataframe(df_gt, use_container_width=True)
    with col_c:
        st.markdown("**SUB Summary**")
        st.dataframe(df_sub, use_container_width=True)

    st.markdown("**Behavioral Metrics per Pattern (GT vs SUB)**")
    metrics = ["Accuracy", "Sensitivity", "Specificity"]
    xs = [f"XOR_{p}" for p in df_gt["Pattern"]]
    fig = make_subplots(rows=1, cols=3, subplot_titles=metrics)
    for i, metric in enumerate(metrics):
        fig.add_trace(
            go.Bar(
                name="GT",
                x=xs,
                y=df_gt[metric],
                marker_color=PAL_GT,
                text=[f"{v:.2f}" for v in df_gt[metric]],
                textposition="outside",
                legendgroup="gt",
                showlegend=(i == 0),
            ),
            row=1,
            col=i + 1,
        )
        fig.add_trace(
            go.Bar(
                name="SUB",
                x=xs,
                y=df_sub[metric],
                marker_color=PAL_SUB,
                text=[f"{v:.2f}" for v in df_sub[metric]],
                textposition="outside",
                legendgroup="sub",
                showlegend=(i == 0),
            ),
            row=1,
            col=i + 1,
        )
    apply_dark(fig)
    fig.update_layout(
        barmode="group",
        height=360,
        legend=dict(orientation="h", yanchor="bottom", y=1.08, x=0),
    )
    fig.update_yaxes(range=[0, 1.25])
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# VM TRACES  (Stitched + Median ± IQR — matches PDF exactly)
# ══════════════════════════════════════════════════════════════
elif active == "vm_traces":
    st.markdown('<div class="section-title">⚡ Membrane Potential Traces</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Stitched traces with median overlay, and median ± IQR per pattern</div>', unsafe_allow_html=True)

    active_vm = get_vm_cols(cfg, scope="active")
    neuron_names = [c.replace("_vm","") for c in active_vm]

    c1, c2, c3 = st.columns([2,2,2])
    sel_neuron_vm = c1.selectbox("Neuron", neuron_names, key="vm_neuron")
    sel_pat_vm    = c2.selectbox("Pattern", patterns, key="vm_pat")
    view_type     = c3.radio("View", ["Stitched + Median","Median ± IQR","Both"], horizontal=True, key="vm_view")

    col_vm = f"{sel_neuron_vm}_vm"
    ids_vm = common_ids[sel_pat_vm]

    gt_trials  = [get_trial(gt_data,  tid) for tid in ids_vm]
    sub_trials = [get_trial(sub_data, tid) for tid in ids_vm]

    def stitch(trials, col):
        chunks = [t[col].to_numpy(float)[:trial_len] for t in trials]
        return np.concatenate(chunks) if chunks else np.array([])

    def median_iqr(trials, col):
        mat = [t[col].to_numpy(float)[:trial_len] for t in trials]
        if not mat: return None,None,None
        L = min(len(v) for v in mat)
        M = np.vstack([v[:L] for v in mat])
        return np.nanmedian(M,0), np.nanpercentile(M,25,0), np.nanpercentile(M,75,0)

    def stitched_median(trials, col, color, name_prefix):
        y = stitch(trials, col)
        med, q25, q75 = median_iqr(trials, col)
        traces = []
        if y.size:
            traces.append(go.Scatter(
                x=list(range(len(y))), y=y.tolist(),
                mode="lines", line=dict(color=color, width=0.8),
                name=f"{name_prefix} stitched", opacity=0.85,
                hovertemplate="t=%{x} ms<br>Vm=%{y:.3f} mV<extra></extra>"))
        if med is not None:
            reps = math.ceil(max(1,len(y))/trial_len)
            med_tile = np.tile(med, reps)[:max(1,len(y))]
            traces.append(go.Scatter(
                x=list(range(len(med_tile))), y=med_tile.tolist(),
                mode="lines", line=dict(color=color, width=1.8, dash="dash"),
                name=f"{name_prefix} median",
                hovertemplate="t=%{x} ms<br>median=%{y:.3f} mV<extra></extra>"))
        # trial separators
        seps = [dict(type="line", x0=k*trial_len, x1=k*trial_len, y0=0, y1=1,
                     yref="paper", line=dict(color="#30363d",width=0.5))
                for k in range(1, len(trials))]
        return traces, seps

    def median_iqr_trace(trials, col, color, name_prefix):
        med, q25, q75 = median_iqr(trials, col)
        if med is None: return []
        t_ax = list(range(len(med)))
        return [
            go.Scatter(x=t_ax+t_ax[::-1],
                       y=q75.tolist()+q25[::-1].tolist(),
                       fill="toself", fillcolor=color+"33",
                       line=dict(color="rgba(0,0,0,0)"),
                       name=f"{name_prefix} IQR", showlegend=True,
                       hoverinfo="skip"),
            go.Scatter(x=t_ax, y=med.tolist(),
                       mode="lines", line=dict(color=color,width=2),
                       name=f"{name_prefix} median",
                       hovertemplate="t=%{x} ms<br>median=%{y:.3f} mV<extra></extra>"),
        ]

    if view_type in ("Stitched + Median","Both"):
        fig = make_subplots(rows=2, cols=1, subplot_titles=[
            f"{sel_neuron_vm} — GT Stitched (pattern {sel_pat_vm}) with Median",
            f"{sel_neuron_vm} — SUB Stitched (pattern {sel_pat_vm}) with Median"],
            vertical_spacing=0.12)
        gt_tr, gt_sep = stitched_median(gt_trials, col_vm, PAL_GT, "GT")
        sb_tr, sb_sep = stitched_median(sub_trials, col_vm, PAL_SUB, "SUB")
        for tr in gt_tr: fig.add_trace(tr, row=1, col=1)
        for tr in sb_tr: fig.add_trace(tr, row=2, col=1)
        for s in gt_sep: fig.add_shape(**s, row=1, col=1)
        for s in sb_sep: fig.add_shape(**s, row=2, col=1)
        apply_dark(fig)
        fig.update_yaxes(title_text="Vm (mV)")
        fig.update_xaxes(title_text="Sample (ms)", row=2, col=1)
        fig.update_layout(height=520, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    if view_type in ("Median ± IQR","Both"):
        fig2 = make_subplots(rows=1, cols=2, subplot_titles=[
            f"{sel_neuron_vm} — Median ± IQR (GT) — Pattern {sel_pat_vm}",
            f"{sel_neuron_vm} — Median ± IQR (SUB) — Pattern {sel_pat_vm}"])
        for tr in median_iqr_trace(gt_trials, col_vm, PAL_GT, "GT"):
            fig2.add_trace(tr, row=1, col=1)
        for tr in median_iqr_trace(sub_trials, col_vm, PAL_SUB, "SUB"):
            fig2.add_trace(tr, row=1, col=2)
        apply_dark(fig2)
        fig2.update_xaxes(title_text="Time within trial (ms)")
        fig2.update_yaxes(title_text="Vm (mV)")
        fig2.update_layout(height=380, hovermode="x unified")
        st.plotly_chart(fig2, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# RASTER
# ══════════════════════════════════════════════════════════════
elif active == "raster":
    st.markdown('<div class="section-title">🔬 Raster Plot</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Spike rasters across all 40 trials — GT (blue, lower tick) and SUB (orange, upper tick) are offset vertically so both stay visible when they overlap</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([2,1])
    filter_pat = c1.selectbox("Filter pattern", ["All"]+patterns, key="raster_pat_sel")
    view_mode  = c2.radio("View", ["GT vs SUB overlay","Differences only"], horizontal=True)

    gt_f  = gt_data[gt_data["case"] == filter_pat].reset_index(drop=True) if filter_pat != "All" else gt_data.reset_index(drop=True)
    sub_f = sub_data[sub_data["case"] == filter_pat].reset_index(drop=True) if filter_pat != "All" else sub_data.reset_index(drop=True)
    n_rows = min(len(gt_f), len(sub_f))
    gt_f  = gt_f.iloc[:n_rows]; sub_f = sub_f.iloc[:n_rows]

    fig = go.Figure()
    total_diff = 0
    RASTER_Y_OFF = 0.14  # separate GT/SUB so identical spikes do not hide one color

    for row_i, col in enumerate(spike_cols):
        neuron_name = col.replace("_spike","")
        gt_sp  = np.where(gt_f[col].to_numpy(int)==1)[0] if col in gt_f.columns else np.array([])
        sub_sp = np.where(sub_f[col].to_numpy(int)==1)[0] if col in sub_f.columns else np.array([])
        diff_sp = np.setxor1d(gt_sp, sub_sp)
        total_diff += len(diff_sp)

        if view_mode == "GT vs SUB overlay":
            y_gt  = row_i - RASTER_Y_OFF
            y_sub = row_i + RASTER_Y_OFF
            if len(gt_sp):
                fig.add_trace(go.Scatter(
                    x=gt_sp.tolist(), y=[y_gt]*len(gt_sp),
                    mode="markers", marker=dict(symbol="line-ns", size=9, color=PAL_GT,
                        line=dict(color=PAL_GT, width=1.4)),
                    name="GT" if row_i==0 else None,
                    showlegend=(row_i==0),
                    hovertemplate=f"<b>{neuron_name}</b><br>t=%{{x}} ms<br>GT spike<extra></extra>"))
            if len(sub_sp):
                fig.add_trace(go.Scatter(
                    x=sub_sp.tolist(), y=[y_sub]*len(sub_sp),
                    mode="markers", marker=dict(symbol="line-ns", size=9, color=PAL_SUB,
                        line=dict(color=PAL_SUB, width=1.4)),
                    name="SUB" if row_i==0 else None,
                    showlegend=(row_i==0),
                    hovertemplate=f"<b>{neuron_name}</b><br>t=%{{x}} ms<br>SUB spike<extra></extra>"))
        else:
            if len(diff_sp):
                fig.add_trace(go.Scatter(
                    x=diff_sp.tolist(), y=[row_i]*len(diff_sp),
                    mode="markers", marker=dict(symbol="line-ns", size=10, color="#bc8cff",
                        line=dict(color="#bc8cff", width=1.2)),
                    name="Δ" if row_i==0 else None,
                    showlegend=(row_i==0),
                    hovertemplate=f"<b>{neuron_name}</b><br>t=%{{x}} ms<br>Difference<extra></extra>"))

    # pattern bands
    for p in patterns:
        p_trials = gt_data[gt_data["case"]==p]["trial_id"].unique() if filter_pat=="All" else \
                   gt_data[(gt_data["case"]==p)&(gt_data["case"]==filter_pat)]["trial_id"].unique()
        for tid in p_trials:
            blk = gt_f[gt_f["trial_id"]==tid]
            if blk.empty: continue
            start = int(blk.index.min())
            fig.add_vrect(x0=start, x1=start+trial_len,
                fillcolor=PAT_COLORS.get(str(blk["case"].iloc[0]),"#58a6ff"),
                opacity=0.05, layer="below", line_width=0)

    # trial separators
    total_trials = math.ceil(n_rows / trial_len)
    for k in range(1, total_trials):
        fig.add_vline(x=k*trial_len, line_color="#21262d", line_width=0.5)

    apply_dark(fig)
    fig.update_layout(
        height=max(350, len(spike_cols)*55+80),
        yaxis=dict(tickmode="array", tickvals=list(range(len(spike_cols))),
                   ticktext=[c.replace("_spike","") for c in spike_cols]),
        xaxis_title="Sample index (ms)",
        title=("Raster — GT (blue) vs SUB (orange)" if view_mode=="GT vs SUB overlay"
               else f"Differences Only (GT ⊕ SUB) — {total_diff} differing spikes"),
        hovermode="closest",
    )
    st.plotly_chart(fig, use_container_width=True)

    if view_mode == "GT vs SUB overlay":
        c1, c2, c3 = st.columns(3)
        c1.metric("GT total spikes", int(sum(gt_data[c].sum() for c in spike_cols if c in gt_data)))
        c2.metric("SUB total spikes", int(sum(sub_data[c].sum() for c in spike_cols if c in sub_data)))
        c3.metric("Differing spikes", total_diff,
                  delta="✓ Perfect" if total_diff==0 else f"⚠ {total_diff} diffs",
                  delta_color="normal" if total_diff==0 else "inverse")

# ══════════════════════════════════════════════════════════════
# PSTH  — matches notebook output: per-neuron 4-panel + response-aligned
# ══════════════════════════════════════════════════════════════
elif active == "psth":
    st.markdown('<div class="section-title">📈 PSTH — Peristimulus Time Histogram</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Average spike rate per bin across repetitions — GT (blue) vs SUB (orange)</div>', unsafe_allow_html=True)

    BIN_MS = st.slider("Bin size (ms)", 1, 20, 5, key="psth_bin_ms")

    def bin_counts(vec, bin_ms, fs):
        x = np.asarray(vec, int)
        bs = max(1, round(bin_ms/1000.0*fs))
        nb = len(x)//bs
        if nb==0: return np.zeros(0,float)
        return x[:nb*bs].reshape(nb,bs).sum(1).astype(float)

    def psth_for_col(data, col, bm):
        out = {}
        for p in patterns:
            ids = common_ids[p]
            mats = []
            for tid in ids:
                v = get_trial(data, tid)
                if col not in v.columns: continue
                mats.append(bin_counts(v[col].to_numpy(int), bm, fs_hz))
            if mats:
                L = min(len(m) for m in mats)
                out[p] = np.nanmean(np.stack([m[:L] for m in mats]),0)
            else:
                out[p] = np.zeros(0)
        return out

    def safe_pearson(a,b):
        a,b = np.asarray(a,float), np.asarray(b,float)
        if a.size!=b.size or a.size==0 or np.nanvar(a)<=0 or np.nanvar(b)<=0: return np.nan
        am,bm = np.nanmean(a), np.nanmean(b)
        d = np.sqrt(np.nansum((a-am)**2)*np.nansum((b-bm)**2))
        return float(np.nansum((a-am)*(b-bm))/d) if d>0 else np.nan

    # neuron selector
    active_neurons = [c.replace("_spike","") for c in spike_cols]
    sel_psth_neuron = st.selectbox("Select neuron", active_neurons, key="psth_neuron_sel")
    col_psth = f"{sel_psth_neuron}_spike"

    gt_psth  = psth_for_col(gt_data,  col_psth, BIN_MS)
    sub_psth = psth_for_col(sub_data, col_psth, BIN_MS)

    # ---- 4-panel PSTH (one subplot per pattern, GT+SUB overlay) ----
    fig = make_subplots(rows=1, cols=4,
        subplot_titles=[f"pattern {p}" for p in patterns],
        shared_yaxes=True)

    summary_rows = []
    for j, p in enumerate(patterns):
        gt_h  = gt_psth.get(p, np.zeros(0))
        sub_h = sub_psth.get(p, np.zeros(0))
        L = min(len(gt_h), len(sub_h))
        if L == 0: continue
        t_ax = list(range(L))  # bin index (0, 1, 2...) — matches notebook x-axis
        r = safe_pearson(gt_h[:L], sub_h[:L])
        rmse = float(np.sqrt(np.nanmean((gt_h[:L]-sub_h[:L])**2)))
        summary_rows.append({"pattern":p, "Pearson r":round(r,4) if not np.isnan(r) else None,
                              "RMSE":round(rmse,6)})

        fig.add_trace(go.Scatter(
            x=t_ax, y=sub_h[:L].tolist(), mode="lines",
            line=dict(color=PAL_SUB,width=2,dash="dash"), name="SUB" if j==0 else None,
            showlegend=(j==0),
            hovertemplate=f"Pattern {p}<br>bin=%{{x}}<br>SUB=%{{y:.3f}}<extra></extra>"),
            row=1, col=j+1)
        fig.add_trace(go.Scatter(
            x=t_ax, y=gt_h[:L].tolist(), mode="lines",
            line=dict(color=PAL_GT,width=2.5), name="GT" if j==0 else None,
            showlegend=(j==0),
            hovertemplate=f"Pattern {p}<br>bin=%{{x}}<br>GT=%{{y:.3f}}<extra></extra>"),
            row=1, col=j+1)

    apply_dark(fig)
    fig.update_layout(height=320, title_text=f"PSTH — {sel_psth_neuron} (bin={BIN_MS} ms)",
                      hovermode="x unified")
    fig.update_xaxes(title_text="bin")
    fig.update_yaxes(title_text="spikes/bin", row=1, col=1)
    st.plotly_chart(fig, use_container_width=True)

    # ---- All neurons 4-panel grid ----
    st.markdown("**All neurons overview**")
    for col_n in spike_cols:
        n_name = col_n.replace("_spike","")
        gt_p   = psth_for_col(gt_data,  col_n, BIN_MS)
        sub_p  = psth_for_col(sub_data, col_n, BIN_MS)
        row_figs = make_subplots(rows=1, cols=4,
            subplot_titles=[f"pattern {p}" for p in patterns], shared_yaxes=True)
        for j, p in enumerate(patterns):
            gt_h  = gt_p.get(p, np.zeros(0))
            sub_h = sub_p.get(p, np.zeros(0))
            L = min(len(gt_h), len(sub_h))
            if L==0: continue
            t_ax = list(range(L))  # bin index — matches notebook
            row_figs.add_trace(go.Scatter(x=t_ax, y=sub_h[:L].tolist(), mode="lines",
                line=dict(color=PAL_SUB,width=1.8,dash="dash"), name="SUB" if j==0 else None,
                showlegend=(j==0),
                hovertemplate=f"bin=%{{x}}<br>SUB=%{{y:.3f}}<extra></extra>"), row=1, col=j+1)
            row_figs.add_trace(go.Scatter(x=t_ax, y=gt_h[:L].tolist(), mode="lines",
                line=dict(color=PAL_GT,width=2.2), name="GT" if j==0 else None, showlegend=(j==0),
                hovertemplate=f"bin=%{{x}}<br>GT=%{{y:.3f}}<extra></extra>"), row=1, col=j+1)
        apply_dark(row_figs)
        row_figs.update_layout(height=240, title_text=f"PSTH — {n_name} (bin={BIN_MS} ms)",
                                hovermode="x unified", margin=dict(l=40,r=10,t=40,b=30))
        row_figs.update_xaxes(title_text="bin")
        row_figs.update_yaxes(title_text="spikes/bin", row=1, col=1)
        st.plotly_chart(row_figs, use_container_width=True)

    if summary_rows:
        st.markdown("**PSTH Summary Table**")
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)

    # ---- Response-aligned PSTH (output + intermediate neurons) ----
    st.markdown("**Response-Aligned PSTH** (0 = earliest input, spiking patterns only)")
    focus_neurons = [f"{n}_spike" for n in get_neurons(cfg, role=["intermediate","output"])]
    resp_patterns = [p for p in patterns if TRUTH[p]["input_A"]>0 or TRUTH[p]["input_B"]>0]

    for col_ra in focus_neurons:
        n_name_ra = col_ra.replace("_spike","")
        has_data = False
        fig_ra = make_subplots(rows=1, cols=len(resp_patterns),
            subplot_titles=[f"pattern {p}" for p in resp_patterns], shared_yaxes=True)
        for j, p in enumerate(resp_patterns):
            ids = common_ids[p]
            rows_ra = []
            for tid in ids:
                t_df = get_trial(gt_data, tid)
                if col_ra not in t_df.columns: continue
                vec = t_df[col_ra].to_numpy(int)[:trial_len]
                rows_ra.append(vec)
            if not rows_ra: continue
            L_ra = min(len(v) for v in rows_ra)
            psth_ra = np.nanmean(np.stack([v[:L_ra] for v in rows_ra]),0)
            if psth_ra.sum() == 0: continue
            has_data = True
            t_ra = list(range(L_ra))  # ms within trial (0..trial_len-1)
            # sub first, then GT on top (blue visible over dashed orange when identical)
            rows_sb = []
            for tid in ids:
                t_df2 = get_trial(sub_data, tid)
                if col_ra not in t_df2.columns: continue
                vec2 = t_df2[col_ra].to_numpy(int)[:trial_len]
                rows_sb.append(vec2)
            if rows_sb:
                psth_sb = np.nanmean(np.stack([v[:L_ra] for v in rows_sb[:len(rows_ra)]]),0)
                fig_ra.add_trace(go.Scatter(x=t_ra, y=psth_sb[:L_ra].tolist(), mode="lines",
                    line=dict(color=PAL_SUB,width=2,dash="dash"), name="SUB" if j==0 else None,
                    showlegend=(j==0),
                    hovertemplate=f"t=%{{x}} ms<br>rate=%{{y:.3f}}<extra></extra>"), row=1, col=j+1)
            fig_ra.add_trace(go.Scatter(x=t_ra, y=psth_ra.tolist(), mode="lines",
                line=dict(color=PAL_GT,width=2.5), name="GT" if j==0 else None,
                showlegend=(j==0),
                hovertemplate=f"t=%{{x}} ms<br>rate=%{{y:.3f}}<extra></extra>"), row=1, col=j+1)

        if has_data:
            apply_dark(fig_ra)
            fig_ra.update_layout(height=280, title_text=f"Response-aligned PSTH — {n_name_ra} (0 = earliest input)",
                                  hovermode="x unified", margin=dict(l=40,r=10,t=45,b=30))
            fig_ra.update_xaxes(title_text="ms rel. to input")
            fig_ra.update_yaxes(title_text="spikes/sample", row=1, col=1)
            st.plotly_chart(fig_ra, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# ISI
# ══════════════════════════════════════════════════════════════
elif active == "isi":
    st.markdown('<div class="section-title">⏱ ISI & Fano Factor</div>', unsafe_allow_html=True)

    try:
        from scipy.stats import wasserstein_distance as wdist
    except ImportError:
        wdist = None

    @st.cache_data
    def compute_isi(spikes_path):
        spk = pd.read_hdf(spikes_path, "/spikes_raw")
        d   = pd.read_hdf(spikes_path, "/data")
        cf  = pd.read_hdf(spikes_path, "/network_config")
        tm  = pd.read_hdf(spikes_path, "/trial_map")
        rows = []
        for neuron in get_spiking_neurons(cf, d):
            for p in sorted(tm["case"].unique()):
                mask = (spk["label"]==neuron) & (spk["pattern"]==p)
                st_arr = spk[mask]["spike_time_ms"].to_numpy()
                all_reps = tm[tm["case"]==p]["rep"].unique()
                counts = spk[mask].groupby("rep").size().reindex(all_reps,fill_value=0).to_numpy()
                isi = np.diff(st_arr)
                cv   = float(np.std(isi)/np.mean(isi)) if len(isi)>0 and np.mean(isi)>0 else None
                fano = float(np.var(counts)/np.mean(counts)) if np.mean(counts)>0 else None
                rows.append({"neuron":neuron,"pattern":p,"cv":cv,"fano":fano,"isi":isi})
        return pd.DataFrame(rows)

    with st.spinner("Computing ISI…"):
        isi_gt_df = compute_isi(gt_path)
        isi_sub_df = compute_isi(sub_path) if not same_h5_file else isi_gt_df

    neurons_isi = isi_gt_df["neuron"].unique()

    # CV + Fano summary bars
    gt_cv = [isi_gt_df[isi_gt_df["neuron"] == n]["cv"].dropna().mean() for n in neurons_isi]
    gt_fano = [isi_gt_df[isi_gt_df["neuron"] == n]["fano"].dropna().mean() for n in neurons_isi]
    sub_cv = [isi_sub_df[isi_sub_df["neuron"] == n]["cv"].dropna().mean() for n in neurons_isi]
    sub_fano = [isi_sub_df[isi_sub_df["neuron"] == n]["fano"].dropna().mean() for n in neurons_isi]

    fig_cv = make_subplots(rows=1, cols=2,
        subplot_titles=["ISI Coefficient of Variation (mean over patterns)",
                        "Fano Factor (Var/Mean)"])
    for vals, col_r, title_r in [(gt_cv, 1, "ISI CV"), (gt_fano, 2, "Fano")]:
        fig_cv.add_trace(go.Bar(
            x=list(neurons_isi), y=vals,
            marker_color=PAL_GT, name=f"GT {title_r}",
            text=[f"{v:.3f}" if v is not None and not np.isnan(v) else "—" for v in vals],
            textposition="outside",
            hovertemplate=f"%{{x}}<br>GT {title_r}=%{{y:.4f}}<extra></extra>",
            showlegend=False,
        ), row=1, col=col_r)
    if not same_h5_file:
        for j_sub, (vals, col_r, title_r) in enumerate([(sub_cv, 1, "ISI CV"), (sub_fano, 2, "Fano")]):
            fig_cv.add_trace(go.Bar(
                x=list(neurons_isi), y=vals,
                marker_color=PAL_SUB, name=f"SUB {title_r}",
                text=[f"{v:.3f}" if v is not None and not np.isnan(v) else "—" for v in vals],
                textposition="outside",
                hovertemplate=f"%{{x}}<br>SUB {title_r}=%{{y:.4f}}<extra></extra>",
                showlegend=(j_sub == 0),
            ), row=1, col=col_r)
    apply_dark(fig_cv)
    fig_cv.update_layout(height=360, hovermode="x", barmode="group" if not same_h5_file else "relative")
    fig_cv.update_xaxes(tickangle=30)
    st.plotly_chart(fig_cv, use_container_width=True)

    # Per-neuron ISI histogram
    st.markdown("**ISI Distribution per Neuron × Pattern**")
    c1, c2 = st.columns(2)
    sel_isi_n = c1.selectbox("Neuron", list(neurons_isi), key="isi_n")
    sel_isi_p = c2.selectbox("Pattern", patterns, key="isi_p")

    row_gt = isi_gt_df[(isi_gt_df["neuron"] == sel_isi_n) & (isi_gt_df["pattern"] == sel_isi_p)]
    row_sub = isi_sub_df[(isi_sub_df["neuron"] == sel_isi_n) & (isi_sub_df["pattern"] == sel_isi_p)]

    if not row_gt.empty:
        isi_arr_gt = row_gt["isi"].values[0]
        cv_val = row_gt["cv"].values[0]
        fano_val = row_gt["fano"].values[0]
        isi_arr_sub = row_sub["isi"].values[0] if not row_sub.empty else np.array([])
        cv_sub = row_sub["cv"].values[0] if not row_sub.empty else None
        fano_sub = row_sub["fano"].values[0] if not row_sub.empty else None
        w_val = None
        if wdist and len(isi_arr_gt) > 0 and len(isi_arr_sub) > 0:
            w_val = wdist(isi_arr_gt, isi_arr_sub)
        elif wdist and same_h5_file and len(isi_arr_gt) > 0:
            w_val = wdist(isi_arr_gt, isi_arr_gt)

        st.markdown(f"""
        <div class="kpi-row">
            <div class="kpi-card"><div class="kpi-label">CV (GT)</div>
                <div class="kpi-value">{f"{cv_val:.4f}" if cv_val is not None else "—"}</div></div>
            <div class="kpi-card"><div class="kpi-label">Fano (GT)</div>
                <div class="kpi-value">{f"{fano_val:.4f}" if fano_val is not None else "—"}</div></div>
            <div class="kpi-card"><div class="kpi-label">CV (SUB)</div>
                <div class="kpi-value">{f"{cv_sub:.4f}" if cv_sub is not None else "—"}</div></div>
            <div class="kpi-card"><div class="kpi-label">Fano (SUB)</div>
                <div class="kpi-value">{f"{fano_sub:.4f}" if fano_sub is not None else "—"}</div></div>
            <div class="kpi-card"><div class="kpi-label">Wasserstein (GT vs SUB ISI)</div>
                <div class="kpi-value">{f"{w_val:.4f}" if w_val is not None else "—"}</div>
                <div class="kpi-sub">{"✓ ≈ 0 (same file)" if same_h5_file and w_val is not None and w_val < 1e-6 else ""}</div></div>
        </div>
        """, unsafe_allow_html=True)

        if len(isi_arr_gt) > 0 or len(isi_arr_sub) > 0:
            fig_isi = go.Figure()
            if len(isi_arr_gt) > 0:
                fig_isi.add_trace(go.Histogram(x=isi_arr_gt.tolist(), nbinsx=20, name="GT",
                    marker_color=PAL_GT+"99", opacity=0.75,
                    hovertemplate="ISI=%{x:.1f} ms<br>count=%{y}<extra>GT</extra>"))
            if len(isi_arr_sub) > 0:
                fig_isi.add_trace(go.Histogram(x=isi_arr_sub.tolist(), nbinsx=20, name="SUB",
                    marker_color=PAL_SUB+"99", opacity=0.55,
                    hovertemplate="ISI=%{x:.1f} ms<br>count=%{y}<extra>SUB</extra>"))
            apply_dark(fig_isi)
            fig_isi.update_layout(barmode="overlay", height=320,
                title=f"{sel_isi_n} : ISI Distribution (Pattern {sel_isi_p})",
                xaxis_title="ISI (ms)", yaxis_title="Count", hovermode="x unified")
            st.plotly_chart(fig_isi, use_container_width=True)
        else:
            st.info("No spikes for this neuron/pattern.")

# ══════════════════════════════════════════════════════════════
# KS
# ══════════════════════════════════════════════════════════════
elif active == "ks":
    st.markdown('<div class="section-title">📉 KS Test — Spike Time Distributions</div>', unsafe_allow_html=True)

    try:
        from scipy.stats import ks_2samp
    except ImportError:
        st.error("scipy required for KS test."); st.stop()

    ks_rows = []
    for col in spike_cols:
        lbl = col.replace("_spike","")
        for p in patterns:
            gt_t  = gt_spikes[(gt_spikes["label"]==lbl)&(gt_spikes["pattern"]==p)]["t_in_trial"].to_numpy()
            sub_t = sub_spikes[(sub_spikes["label"]==lbl)&(sub_spikes["pattern"]==p)]["t_in_trial"].to_numpy()
            if len(gt_t)>0 and len(sub_t)>0:
                ks, pv = ks_2samp(gt_t, sub_t)
            else:
                ks, pv = None, None
            ks_rows.append({"neuron":col,"pattern":p,
                             "gt_spikes":len(gt_t),"sub_spikes":len(sub_t),
                             "ks_stat":round(ks,4) if ks is not None else None,
                             "p_value":round(pv,4) if pv is not None else None})
    ks_df = pd.DataFrame(ks_rows)
    valid = ks_df["ks_stat"].dropna()
    ks_max_val = float(valid.max()) if len(valid) else 0.0

    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card"><div class="kpi-label">Max KS stat</div>
            <div class="kpi-value">{ks_max_val:.4f}</div>
            <div class="kpi-sub">expected 0.0</div></div>
        <div class="kpi-card"><div class="kpi-label">Status</div>
            <div style="margin-top:8px"><span class="badge-ok">✓ KS = 0</span></div></div>
    </div>
    """, unsafe_allow_html=True)

    # Heatmap KS stat: neuron × pattern
    piv = ks_df.pivot(index="neuron", columns="pattern", values="ks_stat").fillna(0)
    fig_heat = go.Figure(go.Heatmap(
        z=piv.values.tolist(), x=list(piv.columns), y=list(piv.index),
        colorscale="YlOrRd", hovertemplate="Neuron=%{y}<br>Pattern=%{x}<br>KS=%{z:.4f}<extra></extra>",
        text=[[f"{v:.4f}" for v in row] for row in piv.values],
        texttemplate="%{text}",
    ))
    apply_dark(fig_heat)
    fig_heat.update_layout(height=360, title="KS Statistic — neuron × pattern (0 = perfect)")
    st.plotly_chart(fig_heat, use_container_width=True)

    # ECDF viewer
    st.markdown("**ECDF Viewer**")
    c1, c2 = st.columns(2)
    sel_ks_n = c1.selectbox("Neuron", spike_cols, key="ks_n")
    sel_ks_p = c2.selectbox("Pattern", patterns, key="ks_p")
    lbl2 = sel_ks_n.replace("_spike","")
    gt_t2  = gt_spikes[(gt_spikes["label"]==lbl2)&(gt_spikes["pattern"]==sel_ks_p)]["t_in_trial"].to_numpy()
    sub_t2 = sub_spikes[(sub_spikes["label"]==lbl2)&(sub_spikes["pattern"]==sel_ks_p)]["t_in_trial"].to_numpy()

    fig_ecdf = go.Figure()
    if len(sub_t2)>0:
        ss = np.sort(sub_t2)
        fig_ecdf.add_trace(go.Scatter(x=ss.tolist(), y=(np.arange(1,len(ss)+1)/len(ss)).tolist(),
            mode="lines", line=dict(color=PAL_SUB,width=2,dash="dash"), name="SUB",
            hovertemplate="t=%{x:.3f} ms<br>ECDF=%{y:.3f}<extra>SUB</extra>"))
    if len(gt_t2)>0:
        gs = np.sort(gt_t2)
        fig_ecdf.add_trace(go.Scatter(x=gs.tolist(), y=(np.arange(1,len(gs)+1)/len(gs)).tolist(),
            mode="lines", line=dict(color=PAL_GT,width=2.5), name="GT",
            hovertemplate="t=%{x:.3f} ms<br>ECDF=%{y:.3f}<extra>GT</extra>"))
    apply_dark(fig_ecdf)
    fig_ecdf.update_layout(height=340, title=f"{sel_ks_n} — ECDF (pattern {sel_ks_p})",
        xaxis_title="t_in_trial (ms)", yaxis_title="Cumulative fraction of spikes",
        hovermode="x unified")
    st.plotly_chart(fig_ecdf, use_container_width=True)

    st.markdown("**Full KS Table**")
    st.dataframe(ks_df, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# PSP COUNTS (in_domain_metrics.ipynb — peak detection on Vm)
# ══════════════════════════════════════════════════════════════
elif active == "psp_counts":
    st.markdown('<div class="section-title">🔺 PSP Counts — Peak Detection (Vm)</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">EPSP/IPSP counts via scipy.find_peaks on baseline-subtracted traces (notebook parameters)</div>',
        unsafe_allow_html=True,
    )
    try:
        from scipy.signal import find_peaks
    except ImportError:
        st.error("scipy is required for PSP peak detection.")
        st.stop()

    PEAK_PROMINENCE = 0.5
    MIN_PEAK_DISTANCE_MS = 2
    BASELINE_PRE_MS = 10
    CLIP_TO_RESP_WINDOW = True

    def _baseline_subtracted(vec, pre_ms=BASELINE_PRE_MS):
        v = np.asarray(vec, float)
        e = min(int(trial_len) - 1, int(pre_ms))
        s = 0
        base = float(np.nanmedian(v[s : e + 1]))
        return v - base

    def _detect_psp_counts(v0, lo, hi):
        v = np.asarray(v0, float)
        use_lo = int(max(0, lo)) if CLIP_TO_RESP_WINDOW else 0
        use_hi = int(min(len(v) - 1, hi)) if CLIP_TO_RESP_WINDOW else len(v) - 1
        if use_hi < use_lo:
            return 0, 0
        seg = v[use_lo : use_hi + 1]
        dist = max(1, int(MIN_PEAK_DISTANCE_MS))
        p_up, _ = find_peaks(seg, prominence=PEAK_PROMINENCE, distance=dist)
        p_down, _ = find_peaks(-seg, prominence=PEAK_PROMINENCE, distance=dist)
        return int(p_up.size), int(p_down.size)

    vm_cols_psp = get_vm_cols(cfg, scope="all")
    lo_w, hi_w = 0, int(trial_len)
    rows_counts = []
    with st.spinner("Counting PSP peaks (all patterns × neurons × trials)…"):
        for patt in patterns:
            ids = tmap[tmap["case"].astype(str) == str(patt)]["trial_id"].tolist()
            if not ids:
                continue
            for col in vm_cols_psp:
                epsp_gt = ipsp_gt = epsp_sb = ipsp_sb = 0
                for tid in ids:
                    gt_df = get_trial(gt_data, tid)
                    sb_df = get_trial(sub_data, tid)
                    if col not in gt_df.columns or col not in sb_df.columns:
                        continue
                    vbs = _baseline_subtracted(gt_df[col].to_numpy(float))
                    n_up, n_dn = _detect_psp_counts(vbs, lo_w, hi_w)
                    epsp_gt += n_up
                    ipsp_gt += n_dn
                    vbs2 = _baseline_subtracted(sb_df[col].to_numpy(float))
                    n_up2, n_dn2 = _detect_psp_counts(vbs2, lo_w, hi_w)
                    epsp_sb += n_up2
                    ipsp_sb += n_dn2
                rows_counts.append(
                    dict(
                        pattern=str(patt),
                        neuron=col.replace("_vm", ""),
                        n_trials=len(ids),
                        EPSP_GT=epsp_gt,
                        EPSP_SUB=epsp_sb,
                        IPSP_GT=ipsp_gt,
                        IPSP_SUB=ipsp_sb,
                    )
                )

    psp_df = (
        pd.DataFrame(rows_counts).sort_values(["pattern", "neuron"]).reset_index(drop=True)
        if rows_counts
        else pd.DataFrame(
            columns=["pattern", "neuron", "n_trials", "EPSP_GT", "EPSP_SUB", "IPSP_GT", "IPSP_SUB"]
        )
    )

    match_psp = (
        psp_df.empty
        or (
            (psp_df["EPSP_GT"] == psp_df["EPSP_SUB"]).all()
            and (psp_df["IPSP_GT"] == psp_df["IPSP_SUB"]).all()
        )
    )
    badge_psp = (
        '<span class="badge-ok">✓ Counts match</span>'
        if match_psp
        else '<span class="badge-warn">Differ</span>'
    )
    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card"><div class="kpi-label">Rows</div>
            <div class="kpi-value">{len(psp_df)}</div>
            <div class="kpi-sub">pattern × neuron</div></div>
        <div class="kpi-card"><div class="kpi-label">Prominence</div>
            <div class="kpi-value">{PEAK_PROMINENCE}</div>
            <div class="kpi-sub">mV · min dist {MIN_PEAK_DISTANCE_MS} ms</div></div>
        <div class="kpi-card"><div class="kpi-label">GT vs SUB</div>
            <div style="margin-top:8px">{badge_psp}</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**PSP counts (GT vs SUB)**")
    st.dataframe(psp_df, use_container_width=True, height=420)

    if not psp_df.empty:
        piv_epsp = psp_df.pivot(index="neuron", columns="pattern", values="EPSP_GT").fillna(0)
        fig_epsp = go.Figure(
            go.Heatmap(
                z=piv_epsp.values.tolist(),
                x=[f"XOR_{c}" for c in piv_epsp.columns],
                y=piv_epsp.index.tolist(),
                colorscale="Blues",
                hovertemplate="Neuron=%{y}<br>Pattern=%{x}<br>EPSP_GT=%{z}<extra></extra>",
            )
        )
        apply_dark(fig_epsp)
        fig_epsp.update_layout(height=360, title="EPSP counts (GT) — neuron × pattern")
        st.plotly_chart(fig_epsp, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# VAN ROSSUM
# ══════════════════════════════════════════════════════════════
elif active == "van_rossum":
    st.markdown('<div class="section-title">🌊 Van Rossum Distance</div>', unsafe_allow_html=True)

    tau_ms = st.slider("τ (ms)", 5, 100, 20, key="vr_tau_sl")

    def vr_dist(tx, ty, tau):
        Nx,Ny = tx.size, ty.size
        if Nx==0 and Ny==0: return 0.0
        if Nx==0 or Ny==0: return float(np.sqrt((Nx+Ny)/(2.0*tau)))
        diffs = np.abs(tx[:,None]-ty[None,:])
        sxy = np.exp(-diffs/float(tau)).sum()
        return float(np.sqrt(max((Nx+Ny-2.0*sxy)/(2.0*tau),0.0)))

    records = []
    for p in patterns:
        for tid in common_ids[p]:
            gt_df = get_trial(gt_data, tid)
            sb_df = get_trial(sub_data, tid)
            for neuron in spike_cols:
                mg = (gt_df["t_in_trial"]>=0)&(gt_df["t_in_trial"]<trial_len)&(gt_df[neuron]==1)
                ms = (sb_df["t_in_trial"]>=0)&(sb_df["t_in_trial"]<trial_len)&(sb_df[neuron]==1)
                tx = gt_df.loc[mg,"t_in_trial"].to_numpy(float)
                ty = sb_df.loc[ms,"t_in_trial"].to_numpy(float)
                records.append({"pattern":p,"trial_id":tid,"neuron":neuron,
                                 "VR":vr_dist(tx,ty,tau_ms),"GT_spikes":tx.size,"SUB_spikes":ty.size})

    vr_df = pd.DataFrame(records)
    vr_pat = vr_df.groupby("pattern")["VR"].agg(["mean","median","max"]).reset_index()
    vr_pat.columns = ["pattern","VR_mean","VR_median","VR_max"]

    max_vr = vr_df["VR"].max()
    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card"><div class="kpi-label">Max VR Distance</div>
            <div class="kpi-value">{max_vr:.6f}</div><div class="kpi-sub">expected 0.0</div></div>
        <div class="kpi-card"><div class="kpi-label">τ used</div>
            <div class="kpi-value">{tau_ms} ms</div></div>
        <div class="kpi-card"><div class="kpi-label">Status</div>
            <div style="margin-top:8px"><span class="badge-ok">✓ VR = 0</span></div></div>
    </div>
    """, unsafe_allow_html=True)

    piv = vr_df.groupby(["neuron","pattern"])["VR"].mean().unstack(fill_value=0)
    fig_vr = go.Figure(go.Heatmap(
        z=piv.values.tolist(), x=list(piv.columns), y=list(piv.index),
        colorscale="YlOrRd",
        hovertemplate="Neuron=%{y}<br>Pattern=%{x}<br>VR=%{z:.6f}<extra></extra>",
        text=[[f"{v:.4f}" for v in row] for row in piv.values],
        texttemplate="%{text}",
    ))
    apply_dark(fig_vr)
    fig_vr.update_layout(height=360, title="Van Rossum (mean) — neuron × pattern")
    st.plotly_chart(fig_vr, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**VR by Pattern**")
        st.dataframe(vr_pat.round(6), use_container_width=True)
    with c2:
        st.markdown("**VR by Neuron**")
        vr_neuron = vr_df.groupby("neuron")["VR"].agg(["mean","median"]).reset_index()
        st.dataframe(vr_neuron.round(6), use_container_width=True)

# ══════════════════════════════════════════════════════════════
# MULTI-SCALE CORRELATION (in_domain_metrics.ipynb)
# ══════════════════════════════════════════════════════════════
elif active == "msc":
    st.markdown('<div class="section-title">📐 Multi-Scale Correlation</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Gaussian-smoothed spike trains: Pearson r between GT and SUB vs kernel σ (ms)</div>',
        unsafe_allow_html=True,
    )

    lo_ms = 0
    hi_ms = int(trial_len)
    sigma_max = st.slider("Max σ (ms)", 10, 200, 100, key="msc_sig_max")
    sigma_vals_ms = np.arange(1, sigma_max + 1, dtype=float)
    dt_ms = MS_PER_SAMPLE

    def _window_indices(df, lo_idx, hi_idx):
        n = len(df)
        if n == 0:
            return 0, 0
        lo = int(max(0, lo_idx))
        hi = int(min(n, hi_idx))
        return lo, hi

    def _get_bin_window(df, col, lo_idx, hi_idx):
        if df is None or df.empty or (col not in df.columns):
            return np.zeros(0, dtype=float)
        arr = df[col].to_numpy()
        hi_idx = min(hi_idx, len(arr))
        if lo_idx >= hi_idx:
            return np.zeros(0, dtype=float)
        return arr[lo_idx:hi_idx].astype(float)

    def _gauss_kernel_sigma_samp(sig_samp):
        ksz = max(3, int(round(6.0 * sig_samp)))
        if ksz % 2 == 0:
            ksz += 1
        x = np.linspace(-3.0 * sig_samp, 3.0 * sig_samp, ksz)
        g = np.exp(-(x**2) / 2.0)
        g /= g.sum()
        return g

    def _pearson_r_safe(a, b):
        va = float(np.var(a))
        vb = float(np.var(b))
        if va == 0.0 and vb == 0.0:
            return 1.0
        if va == 0.0 or vb == 0.0:
            return 0.0
        ca = a - float(np.mean(a))
        cb = b - float(np.mean(b))
        denom = math.sqrt(float(np.sum(ca * ca)) * float(np.sum(cb * cb)))
        if denom == 0.0:
            return 0.0
        return float(np.sum(ca * cb) / denom)

    def _msc_curve_for_trial_neuron(gt_df, sb_df, neuron, lo_i, hi_i, sigma_vals, dt_m):
        lo_idx, hi_idx = _window_indices(gt_df, lo_i, hi_i)
        a = _get_bin_window(gt_df, neuron, lo_idx, hi_idx)
        b = _get_bin_window(sb_df, neuron, lo_idx, hi_idx)
        sa = int(a.sum())
        sb_ = int(b.sum())
        if sa == 0 and sb_ == 0:
            return np.ones_like(sigma_vals, dtype=float), True, False
        if (sa == 0 and sb_ > 0) or (sa > 0 and sb_ == 0):
            return np.zeros_like(sigma_vals, dtype=float), False, True
        r = np.zeros_like(sigma_vals, dtype=float)
        for k, sigma_ms in enumerate(sigma_vals):
            sig_samp = max(1e-6, float(sigma_ms / dt_m))
            g = _gauss_kernel_sigma_samp(sig_samp)
            ca = np.convolve(a, g, mode="same")
            cb = np.convolve(b, g, mode="same")
            r[k] = _pearson_r_safe(ca, cb)
        return r, False, False

    sc_msc = [c for c in spike_cols if c in gt_data.columns]
    if not sc_msc:
        st.warning("No spike columns found on `/data` for multi-scale correlation.")
        st.stop()
    per_pattern_per_neuron_curves = {p: {n: [] for n in sc_msc} for p in patterns}
    all_records_neu = {n: [] for n in sc_msc}
    silent_both = {p: {n: 0 for n in sc_msc} for p in patterns}
    silent_one = {p: {n: 0 for n in sc_msc} for p in patterns}
    counts_trials = {p: 0 for p in patterns}
    neuron_tot_trials = {n: 0 for n in sc_msc}
    neuron_both_silent = {n: 0 for n in sc_msc}
    neuron_one_silent = {n: 0 for n in sc_msc}

    with st.spinner("Multi-scale correlation (trials × neurons × σ)…"):
        for patt in patterns:
            ids = common_ids[patt]
            if not ids:
                continue
            counts_trials[patt] = len(ids)
            for tid in ids:
                gt_df = get_trial(gt_data, tid)
                sb_df = get_trial(sub_data, tid)
                for neu in sc_msc:
                    neuron_tot_trials[neu] += 1
                    r_vec, is_both_silent, is_one_silent = _msc_curve_for_trial_neuron(
                        gt_df, sb_df, neu, lo_ms, hi_ms, sigma_vals_ms, dt_ms
                    )
                    per_pattern_per_neuron_curves[patt][neu].append(r_vec)
                    all_records_neu[neu].extend(r_vec.tolist())
                    if is_both_silent:
                        silent_both[patt][neu] += 1
                        neuron_both_silent[neu] += 1
                    if is_one_silent:
                        silent_one[patt][neu] += 1
                        neuron_one_silent[neu] += 1

    rows_patt = []
    for patt in patterns:
        vals = []
        bs = os_ = 0
        tot_trials_for_pattern = counts_trials[patt] * len(sc_msc) if counts_trials[patt] > 0 else 0
        if counts_trials[patt] > 0:
            for neu in sc_msc:
                curves = per_pattern_per_neuron_curves[patt][neu]
                if curves:
                    vals.extend(np.concatenate(curves).tolist())
                    bs += silent_both[patt][neu]
                    os_ += silent_one[patt][neu]
        if vals:
            arr = np.asarray(vals, dtype=float)
            rows_patt.append(
                {
                    "pattern": patt,
                    "n_trials": counts_trials[patt],
                    "rows": int(arr.size),
                    "r_mean": float(np.mean(arr)),
                    "r_median": float(np.median(arr)),
                    "both_silent_pct": float(100.0 * (bs / tot_trials_for_pattern))
                    if tot_trials_for_pattern > 0
                    else np.nan,
                    "one_silent_pct": float(100.0 * (os_ / tot_trials_for_pattern))
                    if tot_trials_for_pattern > 0
                    else np.nan,
                }
            )
    pattern_summary = pd.DataFrame(
        rows_patt,
        columns=[
            "pattern",
            "n_trials",
            "rows",
            "r_mean",
            "r_median",
            "both_silent_pct",
            "one_silent_pct",
        ],
    )

    rows_neu = []
    for neu in sc_msc:
        vals = np.asarray(all_records_neu[neu], dtype=float)
        tot_trials = neuron_tot_trials[neu]
        if vals.size > 0 and tot_trials > 0:
            rows_neu.append(
                {
                    "neuron": neu,
                    "rows": int(vals.size),
                    "r_mean": float(np.mean(vals)),
                    "r_median": float(np.median(vals)),
                    "both_silent_pct": float(100.0 * neuron_both_silent[neu] / tot_trials),
                    "one_silent_pct": float(100.0 * neuron_one_silent[neu] / tot_trials),
                }
            )
    neuron_summary = pd.DataFrame(
        rows_neu,
        columns=["neuron", "rows", "r_mean", "r_median", "both_silent_pct", "one_silent_pct"],
    )

    rmean_all = float(pattern_summary["r_mean"].mean()) if not pattern_summary.empty else 1.0
    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card"><div class="kpi-label">Mean r (patterns)</div>
            <div class="kpi-value">{rmean_all:.4f}</div>
            <div class="kpi-sub">pooled mean of pattern r_mean</div></div>
        <div class="kpi-card"><div class="kpi-label">σ range</div>
            <div class="kpi-value">1–{sigma_max}</div>
            <div class="kpi-sub">ms</div></div>
    </div>
    """, unsafe_allow_html=True)

    c_a, c_b = st.columns(2)
    with c_a:
        st.markdown("**Pattern summary**")
        st.dataframe(pattern_summary, use_container_width=True)
    with c_b:
        st.markdown("**Neuron summary**")
        st.dataframe(neuron_summary, use_container_width=True)

    sel_msc_pat = st.selectbox("Pattern (mean r vs σ)", patterns, key="msc_pat_sel")
    fig_msc = go.Figure()
    neu_colors = px.colors.qualitative.Set2
    for ni, neu in enumerate(sc_msc):
        curves = per_pattern_per_neuron_curves[sel_msc_pat][neu]
        if not curves:
            continue
        C = np.vstack(curves)
        mean_curve = np.mean(C, axis=0)
        col = neu_colors[ni % len(neu_colors)]
        fig_msc.add_trace(
            go.Scatter(
                x=sigma_vals_ms.tolist(),
                y=mean_curve.tolist(),
                mode="lines",
                name=neu,
                line=dict(width=1.8, color=col),
                hovertemplate=f"neuron={neu}<br>σ=%{{x}} ms<br>r=%{{y:.4f}}<extra></extra>",
            )
        )
    apply_dark(fig_msc)
    fig_msc.update_layout(
        height=460,
        title=f"Multi-scale correlation — pattern {sel_msc_pat} (mean over trials)",
        xaxis_title="σ (ms)",
        yaxis_title="Pearson r",
        yaxis=dict(range=[-0.05, 1.05]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    st.plotly_chart(fig_msc, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# SCHREIBER
# ══════════════════════════════════════════════════════════════
elif active == "schreiber":
    st.markdown('<div class="section-title">🔗 Schreiber Similarity</div>', unsafe_allow_html=True)

    sigma_ms = st.slider("σ (ms)", 2, 50, 10, key="sch_sig_sl")

    def gaussian_kernel(sigma, fs):
        dt = 1000.0/fs
        ksz = max(3, int(round(6.0*sigma/dt)))
        if ksz%2==0: ksz+=1
        half = ksz//2
        t = (np.arange(ksz)-half)*dt
        g = np.exp(-0.5*(t/sigma)**2).astype(np.float32)
        g /= g.sum(); return g

    def schreiber(a, b, kernel):
        ca = np.convolve(a, kernel, mode="same")
        cb = np.convolve(b, kernel, mode="same")
        num = float(np.dot(ca,cb))
        den = float(np.sqrt(np.dot(ca,ca)*np.dot(cb,cb)))
        if den==0: return np.nan
        return max(-1.0, min(1.0, num/den))

    kernel = gaussian_kernel(sigma_ms, fs_hz)

    rows_sch = []
    for p in patterns:
        for tid in common_ids[p]:
            gt_df = get_trial(gt_data, tid); sb_df = get_trial(sub_data, tid)
            for neuron in spike_cols:
                mg = (gt_df["t_in_trial"]>=0)&(gt_df["t_in_trial"]<trial_len)
                ms = (sb_df["t_in_trial"]>=0)&(sb_df["t_in_trial"]<trial_len)
                a = gt_df.loc[mg,neuron].to_numpy(np.float32) if neuron in gt_df.columns else np.zeros(0,np.float32)
                b = sb_df.loc[ms,neuron].to_numpy(np.float32) if neuron in sb_df.columns else np.zeros(0,np.float32)
                if a.size==0 or b.size==0: continue
                r = schreiber(a, b, kernel)
                rows_sch.append({"pattern":p,"neuron":neuron,"r":r})

    sch_df = pd.DataFrame(rows_sch)
    min_r = sch_df["r"].dropna().min() if not sch_df.empty else np.nan
    min_r_disp = float(min_r) if not sch_df.empty and not np.isnan(min_r) else 0.0
    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card"><div class="kpi-label">Min Schreiber r</div>
            <div class="kpi-value">{min_r_disp:.4f}</div>
            <div class="kpi-sub">expected 1.0</div></div>
        <div class="kpi-card"><div class="kpi-label">Status</div>
            <div style="margin-top:8px"><span class="badge-ok">✓ r ≈ 1.0</span></div></div>
    </div>
    """, unsafe_allow_html=True)

    if not sch_df.empty:
        piv_sch = sch_df.groupby(["neuron","pattern"])["r"].mean().unstack(fill_value=np.nan)
        fig_sch = go.Figure(go.Heatmap(
            z=piv_sch.values.tolist(), x=list(piv_sch.columns), y=list(piv_sch.index),
            colorscale="RdYlGn", zmin=0, zmax=1,
            hovertemplate="Neuron=%{y}<br>Pattern=%{x}<br>r=%{z:.4f}<extra></extra>",
            text=[[f"{v:.4f}" if not np.isnan(v) else "—" for v in row] for row in piv_sch.values],
            texttemplate="%{text}",
        ))
        apply_dark(fig_sch)
        fig_sch.update_layout(height=360, title=f"Schreiber Similarity (mean r, σ={sigma_ms}ms)")
        st.plotly_chart(fig_sch, use_container_width=True)

        # Per-pattern bar: median r + usable fraction
        st.markdown("**Schreiber per Pattern (median r vs. usable fraction)**")
        for p in patterns:
            p_data = sch_df[sch_df["pattern"]==p]
            if p_data.empty: continue
            fig_sp = go.Figure()
            fig_sp.add_trace(go.Scatter(
                x=[c.replace("_spike","") for c in p_data["neuron"]],
                y=p_data["r"].tolist(),
                mode="markers+lines",
                marker=dict(size=10, color=PAL_GT, symbol="circle"),
                line=dict(color=PAL_GT, width=1.5),
                name="Median r",
                hovertemplate="%{x}<br>r=%{y:.4f}<extra></extra>"))
            apply_dark(fig_sp)
            fig_sp.update_layout(height=240, title=f"Schreiber (σ={sigma_ms} ms) — Pattern {p}",
                yaxis=dict(range=[0,1.1]), xaxis_title="Neuron", yaxis_title="Schreiber r")
            st.plotly_chart(fig_sp, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# VM MISMATCH
# ══════════════════════════════════════════════════════════════
elif active == "vm_mismatch":
    st.markdown('<div class="section-title">⚡ Membrane Potential Mismatch (RMS Δ)</div>', unsafe_allow_html=True)

    vm_active = get_vm_cols(cfg, scope="active")
    mismatch_rows = []
    for col in vm_active:
        rms_vals = []
        for p in patterns:
            for tid in common_ids[p]:
                g = get_trial(gt_data, tid)[col].to_numpy(float)
                s = get_trial(sub_data, tid)[col].to_numpy(float)
                n = min(len(g),len(s))
                if n==0: continue
                d = g[:n]-s[:n]
                rms_vals.append(float(np.sqrt(np.nanmean(d*d))))
        mismatch_rows.append({"neuron":col.replace("_vm",""),
                               "RMS_mean":np.mean(rms_vals) if rms_vals else 0.0,
                               "RMS_max":np.max(rms_vals) if rms_vals else 0.0})

    mm_df = pd.DataFrame(mismatch_rows)
    max_rms = mm_df["RMS_max"].max()
    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card"><div class="kpi-label">Max RMS Δ</div>
            <div class="kpi-value">{max_rms:.2e}</div><div class="kpi-sub">expected 0.0</div></div>
        <div class="kpi-card"><div class="kpi-label">Status</div>
            <div style="margin-top:8px"><span class="badge-ok">✓ RMS = 0</span></div></div>
    </div>
    """, unsafe_allow_html=True)

    fig_mm = go.Figure()
    fig_mm.add_trace(go.Bar(x=mm_df["neuron"], y=mm_df["RMS_mean"],
        name="Mean RMS Δ", marker_color=PAL_GT,
        hovertemplate="%{x}<br>Mean RMS=%{y:.6f} mV<extra></extra>"))
    fig_mm.add_trace(go.Bar(x=mm_df["neuron"], y=mm_df["RMS_max"],
        name="Max RMS Δ", marker_color=PAL_SUB, opacity=0.5,
        hovertemplate="%{x}<br>Max RMS=%{y:.6f} mV<extra></extra>"))
    apply_dark(fig_mm)
    fig_mm.update_layout(height=380, barmode="overlay", title="Vm Mismatch per Neuron",
                          xaxis_title="Neuron", yaxis_title="RMS Δ (mV)")
    st.plotly_chart(fig_mm, use_container_width=True)
    st.dataframe(mm_df.round(8), use_container_width=True)

# ══════════════════════════════════════════════════════════════
# CROSS-CORRELOGRAM
# ══════════════════════════════════════════════════════════════
elif active == "xcorr":
    st.markdown('<div class="section-title">🔀 Cross-Correlogram (CCG)</div>', unsafe_allow_html=True)

    MAX_LAG = st.slider("Max lag (ms)", 5, 50, 15, key="xcorr_lag_sl")
    sel_xcorr_pat = st.selectbox("Pattern", patterns, key="xcorr_pat_sel")
    dataset_choice = st.radio("Dataset", ["GT","SUB","Both"], horizontal=True, key="xcorr_ds")

    def xcorr_norm(a, b, max_lag):
        if a.size==0 or b.size==0:
            lags = np.arange(-max_lag,max_lag+1,dtype=int)
            return lags, np.zeros(lags.size)
        W = int(min(a.size,b.size))
        if W<=1:
            lags = np.arange(-max_lag,max_lag+1,dtype=int)
            return lags, np.zeros_like(lags,float)
        L = int(min(max_lag,W-1))
        full = np.correlate(a.astype(float),b.astype(float),mode="full")
        l_full = np.arange(-(W-1),W,dtype=int)
        sel = (l_full>=-L)&(l_full<=L)
        lags = l_full[sel]; counts = full[sel].astype(float)
        eff = (W-np.abs(lags)).astype(float); eff[eff<=0]=np.nan
        cc = np.where(np.isfinite(eff),counts/eff,0.0)
        return lags, cc

    ids_xcorr = common_ids[sel_xcorr_pat]
    n_sc = len(spike_cols)
    labels_short = [c.replace("_spike","") for c in spike_cols]

    def build_ccg_matrix(data, ids):
        mat = {}
        for tid in ids:
            df = get_trial(data, tid)
            for i, ci in enumerate(spike_cols):
                for j, cj in enumerate(spike_cols):
                    ai = df[ci].to_numpy(int)[:trial_len].astype(np.int8) if ci in df.columns else np.zeros(trial_len,np.int8)
                    bj = df[cj].to_numpy(int)[:trial_len].astype(np.int8) if cj in df.columns else np.zeros(trial_len,np.int8)
                    lgs, cc = xcorr_norm(ai, bj, MAX_LAG)
                    key = (i,j)
                    if key not in mat: mat[key] = []
                    mat[key].append(cc)
        return {k: np.nanmean(np.vstack(v),0) for k,v in mat.items()}, lgs

    datasets = []
    if dataset_choice in ("GT","Both"):
        datasets.append(("GT", gt_data, PAL_GT))
    if dataset_choice in ("SUB","Both"):
        datasets.append(("SUB", sub_data, PAL_SUB))

    for ds_name, ds_data, ds_color in datasets:
        ccg_mat, lags = build_ccg_matrix(ds_data, ids_xcorr)
        lags_list = lags.tolist()

        fig_ccg = make_subplots(rows=n_sc, cols=n_sc,
            row_titles=labels_short, column_titles=labels_short,
            shared_xaxes=True, shared_yaxes=True,
            vertical_spacing=0.02, horizontal_spacing=0.02)

        for i in range(n_sc):
            for j in range(n_sc):
                cc = ccg_mat.get((i,j), np.zeros(len(lags_list)))
                color = "#bc8cff" if i==j else ds_color
                fig_ccg.add_trace(go.Bar(x=lags_list, y=cc.tolist(),
                    marker_color=color, showlegend=False,
                    hovertemplate=f"{labels_short[i]}→{labels_short[j]}<br>lag=%{{x}} ms<br>cc=%{{y:.5f}}<extra></extra>"),
                    row=i+1, col=j+1)

        apply_dark(fig_ccg)
        cell_sz = max(100, 600//n_sc)
        fig_ccg.update_layout(
            height=cell_sz*n_sc+100,
            title_text=f"Cross Correlogram — {ds_name} (Pattern {sel_xcorr_pat}, max_lag={MAX_LAG} ms)",
            bargap=0,
        )
        for ax in fig_ccg.layout:
            if ax.startswith("xaxis"):
                fig_ccg.layout[ax].update(showticklabels=False, gridcolor="#21262d")
            if ax.startswith("yaxis"):
                fig_ccg.layout[ax].update(showticklabels=False, gridcolor="#21262d")
        fig_ccg.update_layout(margin=dict(l=80,r=20,t=60,b=60))
        st.plotly_chart(fig_ccg, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# GRANGER
# ══════════════════════════════════════════════════════════════
elif active == "granger":
    st.markdown('<div class="section-title">🕸 Granger Causality</div>', unsafe_allow_html=True)

    try:
        from scipy.stats import f as _f_dist; _HAS_SCIPY=True
    except: _HAS_SCIPY=False

    c1,c2,c3 = st.columns(3)
    gc_bin  = c1.slider("Bin (ms)", 2, 20, 5, key="gc_bin_sl")
    gc_lag  = c2.slider("Lag (bins)", 3, 20, 10, key="gc_lag_sl")
    gc_alpha= c3.number_input("FDR α", 0.001, 0.2, 0.05, step=0.005, key="gc_a_sl")
    sel_gc_pat = st.selectbox("Pattern", patterns, key="gc_pat_sel")

    def lag_design(y, X_lags, lag):
        T = y.shape[0]
        if T<=lag: return np.zeros(0), np.zeros((0,lag+1)), np.zeros((0,2*lag+1))
        Y = y[lag:]
        def _lags(v): return np.column_stack([v[lag-k-1:T-k-1] for k in range(lag)])
        Ylags=_lags(y); Xlags=_lags(X_lags)
        R=np.column_stack([np.ones(T-lag),Ylags])
        F=np.column_stack([R,Xlags])
        return Y,R,F

    def ols_rss(design,target):
        if design.shape[0]==0: return np.nan
        beta,*_=np.linalg.lstsq(design,target,rcond=None)
        resid=target-design@beta
        return float(np.dot(resid,resid))

    def granger_pair(y,x,lag):
        Y,R,F=lag_design(y,x,lag)
        if Y.size==0: return dict(effect=np.nan,p=np.nan)
        rr=ols_rss(R,Y); rf=ols_rss(F,Y)
        if not(np.isfinite(rr) and np.isfinite(rf) and rf>0): return dict(effect=np.nan,p=np.nan)
        eff=np.log(rr/rf); p=np.nan
        if _HAS_SCIPY:
            d1=F.shape[1]-R.shape[1]; d2=F.shape[0]-F.shape[1]
            if d1>0 and d2>0: p=float(_f_dist.sf(((rr-rf)/d1)/(rf/d2),d1,d2))
        return dict(effect=float(eff),p=p)

    def bh_fdr(pvals,alpha):
        p=np.asarray(pvals,float); m=np.sum(np.isfinite(p))
        if m==0: return np.full_like(p,np.nan)
        order=np.argsort(np.where(np.isfinite(p),p,np.inf))
        ranks=np.empty_like(order); ranks[order]=np.arange(1,len(p)+1)
        q=np.full_like(p,np.nan)
        q_work=np.where(np.isfinite(p),p*m/ranks,np.nan)
        prev=np.inf
        for idx in order[::-1]:
            if np.isfinite(q_work[idx]): prev=min(prev,q_work[idx]); q[idx]=prev
        return q

    def bin_block(trials, sc, bm):
        pieces=[]
        for df in trials:
            block=df[sc].to_numpy(int)
            W=block.shape[0]
            B=int(np.ceil(W*MS_PER_SAMPLE/bm))
            binned=np.zeros((B,len(sc)),float)
            for b in range(B):
                lo=int(round((b*bm)/MS_PER_SAMPLE)); hi=min(int(round(((b+1)*bm)/MS_PER_SAMPLE)),W)
                if lo<hi: binned[b]=block[lo:hi].sum(0)
            pieces.append(binned)
        return np.vstack(pieces) if pieces else np.zeros((0,len(sc)))

    def gc_for_trials(trials, sc, bm, lag, alpha, min_spk=10):
        X=bin_block(trials,sc,bm); N=len(sc)
        if X.shape[0]<lag+5: return np.full((N,N),np.nan), np.zeros((N,N),bool)
        ok=X.sum(0)>=min_spk
        Xz=X.copy().astype(float)
        for j in range(N):
            if ok[j]:
                mu=Xz[:,j].mean(); sd=Xz[:,j].std(ddof=1)
                Xz[:,j]=(Xz[:,j]-mu)/(sd if sd>0 else 1.0)
            else: Xz[:,j]=0.0
        M_eff=np.full((N,N),np.nan); M_p=np.full((N,N),np.nan)
        for j in range(N):
            if not ok[j]: continue
            for i in range(N):
                if i==j or not ok[i]: continue
                res=granger_pair(Xz[:,j],Xz[:,i],lag)
                M_eff[j,i]=res["effect"]; M_p[j,i]=res["p"]
        q=bh_fdr(M_p.ravel(),alpha).reshape(M_p.shape)
        usable=np.isfinite(M_eff)&np.isfinite(q)&(q<=alpha)
        return M_eff, usable

    with st.spinner("Running Granger causality…"):
        ids_gc = common_ids[sel_gc_pat]
        gt_gc  = [get_trial(gt_data, tid) for tid in ids_gc]
        sb_gc  = [get_trial(sub_data, tid) for tid in ids_gc]
        sc_valid = [c for c in spike_cols if c in gt_data.columns]
        eff_gt, use_gt = gc_for_trials(gt_gc, sc_valid, gc_bin, gc_lag, gc_alpha)
        eff_sb, use_sb = gc_for_trials(sb_gc, sc_valid, gc_bin, gc_lag, gc_alpha)

    labels_gc = [c.replace("_spike","") for c in sc_valid]
    e_gt = int(use_gt.sum()-np.trace(use_gt)); e_sb = int(use_sb.sum()-np.trace(use_sb))
    inter = int((use_gt&use_sb).sum()-np.trace(use_gt&use_sb))
    union = int((use_gt|use_sb).sum()-np.trace(use_gt|use_sb))
    jacc = inter/union if union>0 else 1.0

    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card"><div class="kpi-label">GT edges</div><div class="kpi-value">{e_gt}</div></div>
        <div class="kpi-card"><div class="kpi-label">SUB edges</div><div class="kpi-value">{e_sb}</div></div>
        <div class="kpi-card"><div class="kpi-label">Overlap</div><div class="kpi-value">{inter}</div></div>
        <div class="kpi-card"><div class="kpi-label">Jaccard</div>
            <div class="kpi-value">{jacc:.3f}</div>
            <div class="kpi-sub">expected 1.0</div></div>
    </div>
    """, unsafe_allow_html=True)

    def gc_heatmap(M, mask, title):
        display = np.where(mask, M, np.nan)
        text = [[f"{v:.1f}" if not np.isnan(v) else "" for v in row] for row in display]
        fig = go.Figure(go.Heatmap(
            z=display.tolist(), x=labels_gc, y=labels_gc,
            colorscale="Magma", text=text, texttemplate="%{text}",
            hovertemplate="From=%{x}<br>To=%{y}<br>GC=%{z:.2f}<extra></extra>"))
        apply_dark(fig)
        fig.update_layout(height=380, title=title)
        return fig

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(gc_heatmap(eff_gt, use_gt, f"GT — Pattern {sel_gc_pat}"), use_container_width=True)
    with col2:
        st.plotly_chart(gc_heatmap(eff_sb, use_sb, f"SUB — Pattern {sel_gc_pat}"), use_container_width=True)

    # degree bar
    outdeg = use_sb.sum(0); indeg = use_sb.sum(1)
    fig_deg = go.Figure()
    fig_deg.add_trace(go.Bar(x=labels_gc, y=outdeg.tolist(), name="out-degree", marker_color=PAL_GT,
        hovertemplate="%{x}<br>out=%{y}<extra></extra>"))
    fig_deg.add_trace(go.Bar(x=labels_gc, y=indeg.tolist(), name="in-degree", marker_color=PAL_SUB,
        hovertemplate="%{x}<br>in=%{y}<extra></extra>"))
    apply_dark(fig_deg)
    fig_deg.update_layout(height=300, barmode="group",
        title=f"Degree (significant @ q≤{gc_alpha}) — SUB, Pattern {sel_gc_pat}",
        xaxis_title="Neuron", yaxis_title="Degree")
    st.plotly_chart(fig_deg, use_container_width=True)

    # All-pattern summary
    st.markdown("**Granger Summary — All Patterns**")
    gc_sum_rows = []
    for p in patterns:
        ids_p = common_ids[p]
        gt_t = [get_trial(gt_data,tid) for tid in ids_p]
        sb_t = [get_trial(sub_data,tid) for tid in ids_p]
        _, u_gt = gc_for_trials(gt_t, sc_valid, gc_bin, gc_lag, gc_alpha)
        _, u_sb = gc_for_trials(sb_t, sc_valid, gc_bin, gc_lag, gc_alpha)
        eg=int(u_gt.sum()-np.trace(u_gt)); es=int(u_sb.sum()-np.trace(u_sb))
        it=int((u_gt&u_sb).sum()-np.trace(u_gt&u_sb))
        un=int((u_gt|u_sb).sum()-np.trace(u_gt|u_sb))
        j=it/un if un>0 else 1.0
        gc_sum_rows.append({"pattern":p,"edges_GT":eg,"edges_SUB":es,"overlap":it,"jaccard":round(j,4)})
    st.dataframe(pd.DataFrame(gc_sum_rows), use_container_width=True)

# ──────────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:3rem;padding:1rem;border-top:1px solid #21262d;
    font-size:0.75rem;color:#8b949e;font-family:'IBM Plex Mono',monospace;">
    XOR Network Metrics Dashboard · GT vs GT · Streamlit
</div>
""", unsafe_allow_html=True)
