"""
XOR Neural Network Metrics Dashboard
=====================================
Run:  streamlit run xor_dashboard.py
Place groundtruth.h5 in the same directory as this script (or set paths in the sidebar).
Optional: network_config.json with a truth_table block (same layout as in_domain_metrics.ipynb)
next to the H5 or under GT / output/GT — overrides the built-in XOR truth table for metrics.
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import h5py, html, importlib.util, json, os, math
from datetime import datetime


def _load_pdf_generator():
    """Load pdf_report.py from beside this script (or repo METRICS/)."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, "pdf_report.py"),
        os.path.join(script_dir, "pdfreport.py"),
        os.path.normpath(os.path.join(script_dir, "..", "METRICS", "pdf_report.py")),
        os.path.normpath(os.path.join(script_dir, "..", "..", "METRICS", "pdf_report.py")),
    ]
    module_path = next((p for p in candidates if os.path.isfile(p)), None)
    if module_path is None:
        return None, (
            "pdf_report.py is missing. Copy METRICS/pdf_report.py into the same "
            f"folder as dashboard.py ({script_dir})."
        )
    try:
        spec = importlib.util.spec_from_file_location("xor_pdf_report", module_path)
        if spec is None or spec.loader is None:
            return None, f"Could not load PDF module from {module_path}"
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not getattr(mod, "_HAS_REPORTLAB", True):
            return None, (
                "reportlab is not installed in the Python environment that runs Streamlit. "
                "Run: python -m pip install reportlab"
            )
        fn = getattr(mod, "generate_pdf_report", None)
        if fn is None:
            return None, f"generate_pdf_report() not found in {module_path}"
        return fn, None
    except Exception as exc:
        return None, f"PDF module error: {exc}"


generate_pdf_report, PDF_EXPORT_ERROR = _load_pdf_generator()


def _load_scoring_module():
    """Load dashboard_scoring.py from beside this script (or repo METRICS/)."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, "dashboard_scoring.py"),
        os.path.normpath(os.path.join(script_dir, "..", "METRICS", "dashboard_scoring.py")),
        os.path.normpath(os.path.join(script_dir, "..", "..", "METRICS", "dashboard_scoring.py")),
    ]
    module_path = next((p for p in candidates if os.path.isfile(p)), None)
    if module_path is None:
        return None, "dashboard_scoring.py is missing beside dashboard.py."
    try:
        spec = importlib.util.spec_from_file_location("xor_dashboard_scoring", module_path)
        if spec is None or spec.loader is None:
            return None, f"Could not load scoring module from {module_path}"
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        fn = getattr(mod, "compute_overall_score", None)
        if fn is None:
            return None, f"compute_overall_score() not found in {module_path}"
        return fn, None
    except Exception as exc:
        return None, f"Scoring module error: {exc}"


compute_overall_score_fn, SCORING_ERROR = _load_scoring_module()

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

/* Plotly legend / axis text on dark charts */
.js-plotly-plot .plotly .legend text,
.js-plotly-plot .plotly .gtitle,
.js-plotly-plot .plotly .xtitle,
.js-plotly-plot .plotly .ytitle,
.js-plotly-plot .plotly .xtick text,
.js-plotly-plot .plotly .ytick text {
    fill: #e6edf3 !important;
}

/* Plotly hover tooltips — force dark text on light box (all chart types) */
.js-plotly-plot .hoverlayer text,
.js-plotly-plot .hoverlayer tspan,
.js-plotly-plot .hoverlayer .nums,
.js-plotly-plot .hoverlayer .hovertext,
.js-plotly-plot .hoverlayer .hovertext text,
.js-plotly-plot .hoverlayer .hovertext tspan {
    fill: #111827 !important;
    color: #111827 !important;
    font-weight: 500 !important;
}
.js-plotly-plot .hoverlayer rect,
.js-plotly-plot .hoverlayer path.bg {
    fill: #f8fafc !important;
    fill-opacity: 0.98 !important;
    stroke: #374151 !important;
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
.metric-panel .metric-tips {
    color: #8b949e; font-size: 0.88rem; margin-top: 6px; line-height: 1.45;
}
.metric-panel .metric-run {
    margin-top: 10px; padding-top: 8px; border-top: 1px solid #30363d;
}
.table-scroll-wrap {
    overflow: auto; border: 1px solid #30363d; border-radius: 6px; margin: 8px 0;
}
.table-scroll-wrap table {
    width: 100%; border-collapse: collapse; font-size: 0.85rem;
}
.table-scroll-wrap thead th {
    position: sticky; top: 0; z-index: 2;
    background: #161b22 !important; color: #e6edf3 !important;
    border-bottom: 1px solid #30363d; padding: 8px 10px; text-align: left;
}
.table-scroll-wrap tbody td {
    padding: 6px 10px; border-bottom: 1px solid #21262d; color: #c9d1d9;
}

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

/* PDF export — sidebar only (avoids overlapping Deploy / Rerun in header) */
[data-testid="stSidebar"] .st-key-download_pdf_report [data-testid="stDownloadButton"],
[data-testid="stSidebar"] .st-key-download_pdf_report button {
    width: 100% !important;
    background: #161b22 !important;
    color: #e6edf3 !important;
    border: 1px solid #30363d !important;
    border-radius: 0.5rem !important;
    font-size: 0.8125rem !important;
    padding: 0.35rem 0.8rem !important;
    min-height: 2.25rem !important;
    line-height: 1.2 !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .st-key-download_pdf_report button:hover {
    border-color: #388bfd !important;
    color: #58a6ff !important;
}
[data-testid="stSidebar"] .pdf-sidebar-status {
    display: block;
    padding: 0.35rem 0.5rem;
    background: #161b22;
    color: #8b949e;
    border: 1px solid #30363d;
    border-radius: 0.5rem;
    font-size: 0.8125rem;
    text-align: center;
}

/* st.table — dark theme, no Glide toolbar (avoids grey hover boxes) */
[data-testid="stTable"] {
    width: 100% !important;
}
[data-testid="stTable"] table {
    width: 100% !important;
    background-color: #161b22 !important;
    color: #e6edf3 !important;
    border-collapse: collapse !important;
}
[data-testid="stTable"] th {
    background-color: #0d1117 !important;
    color: #e6edf3 !important;
    border: 1px solid #30363d !important;
    padding: 8px 12px !important;
    font-weight: 600 !important;
}
[data-testid="stTable"] td {
    background-color: #161b22 !important;
    color: #e6edf3 !important;
    border: 1px solid #21262d !important;
    padding: 8px 12px !important;
}

/* Element toolbar icons only (not Plotly trace paths) */
[data-testid="stElementToolbar"] button,
[data-testid="stDataFrame"] [data-testid="stElementToolbar"] button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
[data-testid="stElementToolbar"] button svg path {
    fill: #c9d1d9 !important;
}
[data-testid="stElementToolbar"] button:hover {
    background: rgba(88, 166, 255, 0.12) !important;
}
[data-testid="stElementToolbar"] button:hover svg path {
    fill: #58a6ff !important;
}
.js-plotly-plot .plotly .modebar-btn {
    background: transparent !important;
}
.js-plotly-plot .plotly .modebar-btn path {
    fill: #c9d1d9 !important;
}
.js-plotly-plot .plotly .modebar-btn:hover path {
    fill: #58a6ff !important;
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
    hoverlabel=dict(
        bgcolor="#f8fafc",
        bordercolor="#374151",
        font=dict(color="#111827", family="IBM Plex Sans", size=13),
    ),
)

HOVER_LABEL = dict(
    bgcolor="#f8fafc",
    bordercolor="#374151",
    font=dict(color="#111827", family="IBM Plex Sans", size=13),
)

PAL_GT  = "#58a6ff"   # blue  – GT
PAL_SUB = "#f0883e"   # orange – SUB
PAL_GT_FILL = "rgba(88, 166, 255, 0.75)"
PAL_SUB_FILL = "rgba(240, 136, 62, 0.55)"
PAL_VM_MEAN = "#58a6ff"
PAL_VM_MAX = "#d29922"
PAL_GC_OUT = "#58a6ff"
PAL_GC_IN = "#3fb950"
PAL_AUTO = "#bc8cff"
PAL_ACC = ["#58a6ff","#3fb950","#f0883e","#ffa657"]
PAT_COLORS = {"00":"#58a6ff","11":"#3fb950","01":"#ffa657","10":"#f0883e"}


def _hex_rgba(hex_color: str, alpha: float = 0.2) -> str:
    """Plotly fillcolor must be rgba()/rgb()/6-digit hex — not 8-digit #RRGGBBAA."""
    h = str(hex_color).lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        return f"rgba(88, 166, 255, {alpha})"
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def _shared_hist_xbins(arrays, n_bins=20):
    """Align GT/SUB histogram bins so bars are comparable and colors stay distinct."""
    parts = [np.asarray(a).ravel() for a in arrays if a is not None and len(np.asarray(a).ravel()) > 0]
    if not parts:
        return dict(start=0, end=1, size=1)
    combined = np.concatenate(parts)
    lo, hi = float(np.min(combined)), float(np.max(combined))
    if hi <= lo:
        hi = lo + 1.0
    pad = max((hi - lo) * 0.05, 1.0)
    lo -= pad * 0.5
    hi += pad * 0.5
    size = (hi - lo) / n_bins
    return dict(start=lo, end=hi + size * 1e-6, size=size)


def _add_gt_sub_histogram(fig, x_gt, x_sub, n_bins=20, hover_x_label="ISI"):
    """Grouped GT/SUB histogram — no blended third color from overlay + mismatched bins."""
    gt = np.asarray(x_gt).ravel() if x_gt is not None and len(x_gt) else np.array([])
    sub = np.asarray(x_sub).ravel() if x_sub is not None and len(x_sub) else np.array([])
    xbins = _shared_hist_xbins([gt, sub], n_bins=n_bins)
    if len(gt):
        fig.add_trace(go.Histogram(
            x=gt.tolist(), xbins=xbins, name="GT",
            marker=dict(color=PAL_GT, line=dict(color=PAL_GT, width=1)),
            hovertemplate=f"{hover_x_label}=%{{x:.1f}} ms<br>count=%{{y}}<extra>GT</extra>",
        ))
    if len(sub):
        fig.add_trace(go.Histogram(
            x=sub.tolist(), xbins=xbins, name="SUB",
            marker=dict(color=PAL_SUB, line=dict(color=PAL_SUB, width=1)),
            hovertemplate=f"{hover_x_label}=%{{x:.1f}} ms<br>count=%{{y}}<extra>SUB</extra>",
        ))

def dark_fig(**kw):
    fig = go.Figure(**kw)
    fig.update_layout(**DARK)
    return fig

def apply_dark(fig):
    fig.update_layout(**DARK)
    try:
        fig.update_traces(hoverlabel=HOVER_LABEL)
    except (ValueError, TypeError):
        pass
    return fig


METRIC_GUIDES = {
    "overview": {
        "title": "Overview",
        "summary": (
            "Experiment summary: neurons, trials, XOR patterns. "
            "Pipeline KPIs (I/O Vm RMSE, Van Rossum, Schreiber) score how close SUB is to GT on "
            "<b>input/output neurons only</b> — not deep interneurons."
        ),
        "tips": (
            "Focus KPIs on <b>PyrIn_A, B1, B2, E</b>. "
            "Vm RMSE = voltage error (mV); Van Rossum = spike-timing distance on E; Schreiber = spike-shape similarity on E."
        ),
    },
    "behavioral": {
        "title": "Behavioral Accuracy",
        "summary": (
            "Did output neuron <b>E</b> implement the XOR truth table? "
            "Compares SUB firing (≥1 spike in trial) vs expected 0/1 per pattern "
            "(00, 01, 10, 11). <b>Most important pass/fail metric</b> for black-box SUB."
        ),
        "tips": (
            "Counts are trials per pattern (10 = all reps agree). "
            "Target: SUB accuracy 100% on 00, 01, 10, 11. "
            "Checks <b>if E fired</b>, not exact spike timing."
        ),
    },
    "raster": {
        "title": "Raster Plot",
        "summary": (
            "Every spike as a tick: GT (blue, lower) vs SUB (orange, upper). "
            "Purple/mixed = mismatch. Focus on <b>E</b> and inputs; "
            "GT-only ticks on PyrMid/Int are normal for black-box SUB."
        ),
        "tips": (
            "Blue = GT, orange = SUB (offset vertically). "
            "Match on <b>E</b> and inputs; GT-only ticks on PyrMid/Int are normal for black-box."
        ),
    },
    "vm_traces": {
        "title": "Membrane Potential Traces",
        "summary": (
            "Continuous voltage (mV) on selected neuron. "
            "GT and SUB panels share <b>linked zoom/pan</b> on the time axis. "
            "Compare I/O neurons (PyrIn_A, B1, B2, E) — interneurons may be flat in SUB."
        ),
        "tips": (
            "Stitched = all reps with dashed median; Median ± IQR = typical ± spread. "
            "Good overlap on mapped I/O; flat −60 mV on inputs is bad."
        ),
    },
    "psth": {
        "title": "PSTH",
        "summary": (
            "Average spikes per time bin across repetitions — when does this neuron tend to fire? "
            "Compare GT vs SUB per XOR pattern. Check <b>E</b> and inputs first."
        ),
        "tips": (
            "Peaks at the same bin = good timing. "
            "Summary table Pearson r / RMSE quantify curve similarity."
        ),
    },
    "isi": {
        "title": "ISI / Fano",
        "summary": (
            "<b>ISI</b> = gap between consecutive spikes; <b>CV</b> measures regularity. "
            "<b>Fano</b> = variability of spike counts across trials. "
            "Useful on neurons that actually fire in both GT and SUB."
        ),
        "tips": (
            "Wasserstein 0 = same ISI spacing. CV ≈ 1 is Poisson-like. "
            "Silent interneurons in SUB are not informative."
        ),
    },
    "ks": {
        "title": "KS Test",
        "summary": (
            "Kolmogorov–Smirnov: are GT and SUB spike times from the same distribution? "
            "<b>KS = 0</b> perfect; <b>KS = 1</b> completely different. "
            "Heatmap shows neuron × pattern; focus on E and inputs."
        ),
        "tips": (
            "ECDF curves on top of each other → KS ≈ 0. "
            "Focus <b>E</b> and input rows; long table scrolls with fixed header."
        ),
    },
    "psp_counts": {
        "title": "PSP Counts",
        "summary": (
            "Counts sub-threshold voltage bumps (EPSP/IPSP) via peak detection on Vm. "
            "Measures synaptic events below full spikes. Best interpreted on <b>I/O Vm</b>."
        ),
        "tips": (
            "Prominence ≥ 0.5 mV, min distance 2 ms. "
            "Compare mapped neurons; GT interneuron PSP structure often absent in SUB."
        ),
    },
    "van_rossum": {
        "title": "Van Rossum Distance",
        "summary": (
            "Single number for spike-train timing difference (τ controls time scale). "
            "<b>0 = identical</b>. Primary timing metric on output <b>E</b>."
        ),
        "tips": (
            "Small τ = strict timing. Good: near 0 on E. "
            "High VR on internals while E is fine is expected for black-box."
        ),
    },
    "msc": {
        "title": "Multi-Scale Correlation",
        "summary": (
            "Pearson r between smoothed GT and SUB spike trains vs blur width σ. "
            "Shows whether match holds at fine or only coarse time scales."
        ),
        "tips": (
            "Flat near 1.0 = match at all scales. "
            "Low on PyrMid/Int in SUB is expected; judge <b>E</b> first."
        ),
    },
    "schreiber": {
        "title": "Schreiber Similarity",
        "summary": (
            "Correlation of Gaussian-smoothed spike trains. "
            "<b>r = 1</b> identical shape; <b>r = 0</b> unrelated. "
            "Reported on output E in Overview."
        ),
        "tips": (
            "Complements Van Rossum (similarity vs distance). "
            "Dash in heatmap = both silent, nothing to compare."
        ),
    },
    "vm_mismatch": {
        "title": "Vm Mismatch (RMS Δ)",
        "summary": (
            "Root-mean-square voltage difference GT − SUB per neuron, pooled over patterns. "
            "<b>0 = identical Vm</b>. Check mapped I/O neurons."
        ),
        "tips": (
            "Blue = mean RMS, orange = worst trial. "
            "Good on PyrIn; large Int/PyrMid values are SUB placeholders (−60 mV)."
        ),
    },
    "xcorr": {
        "title": "Cross-Correlogram",
        "summary": (
            "Who tends to fire before whom (lagged correlation). "
            "Diagonal = autocorrelation. Compare GT vs SUB choreography on <b>I/O cells</b>."
        ),
        "tips": (
            "Peak at lag 0 = synchronous. Compare GT vs SUB on E ↔ inputs. "
            "Flat Int/PyrMid on SUB is expected."
        ),
    },
    "granger": {
        "title": "Granger Causality",
        "summary": (
            "Statistical map: does neuron A's past help predict B's future? "
            "<b>Not biological wiring</b> — predictive structure in data. "
            "Low Jaccard vs GT is <b>expected</b> for black-box SUB."
        ),
        "tips": (
            "Jaccard = edge overlap GT vs SUB. SUB often shows only input→E links. "
            "Tier-3 diagnostic — not primary pass/fail for black-box."
        ),
    },
}


def show_metric_panel(key, result_lines=None, verdict="neutral"):
    """Single info box: what the metric means + tips + this-run interpretation."""
    g = METRIC_GUIDES.get(key)
    badge = ""
    if verdict == "ok":
        badge = ' <span class="badge-ok">✓ looks good</span>'
    elif verdict == "warn":
        badge = ' <span class="badge-warn">⚠ review</span>'
    parts = []
    if g:
        parts.append(f"<b>{g['title']}</b> — {g['summary']}")
        tips = g.get("tips") or g.get("detail")
        if tips:
            parts.append(f"<div class='metric-tips'>{tips}</div>")
    if result_lines:
        run_body = "<br>".join(f"• {ln}" for ln in result_lines if ln)
        parts.append(f"<div class='metric-run'><b>This run</b>{badge}<br>{run_body}</div>")
    elif badge:
        parts.append(f"<div class='metric-run'>{badge}</div>")
    if parts:
        st.markdown(
            f"<div class='info-box metric-panel'>{''.join(parts)}</div>",
            unsafe_allow_html=True,
        )


def show_metric_guide(key):
    """Backward-compatible alias — static guide only."""
    show_metric_panel(key)


def show_dynamic_result(lines, verdict="neutral"):
    """Backward-compatible alias — results only (prefer show_metric_panel)."""
    if lines:
        badge = ""
        if verdict == "ok":
            badge = ' <span class="badge-ok">✓ looks good</span>'
        elif verdict == "warn":
            badge = ' <span class="badge-warn">⚠ review</span>'
        run_body = "<br>".join(f"• {ln}" for ln in lines if ln)
        st.markdown(
            f"<div class='info-box metric-panel'>"
            f"<div class='metric-run'><b>This run</b>{badge}"
            f"<br>{run_body}</div></div>",
            unsafe_allow_html=True,
        )


def _out_spike_col(cfg, data):
    cols = get_spike_cols(cfg, data, role="output")
    return cols[0] if cols else "E_spike"


def _io_spike_cols(all_cols):
    want = {f"{n}_spike" for n in ("PyrIn_A", "PyrIn_B1", "PyrIn_B2", "E")}
    return [c for c in all_cols if c in want]


def _verdict_from_acc(acc):
    if acc >= 0.999:
        return "ok"
    if acc >= 0.9:
        return "warn"
    return "warn"


def _insight_sub(overall_acc=None, gt_sub_match=None, ks_max=None, vr_max=None,
                 rmse=None, sch_r=None, jaccard=None, wasserstein=None, msc_r=None,
                 raster_diff=None, psp_io_mismatch=None):
    """One-line conclusion for KPI cards."""
    if overall_acc is not None:
        if overall_acc >= 0.999:
            return "Conclusion: SUB passes XOR on all trials."
        if overall_acc >= 0.9:
            return "Conclusion: mostly correct — inspect failing patterns in table."
        return "Conclusion: SUB fails XOR — fix before timing/Vm metrics."
    if gt_sub_match is not None:
        return ("Conclusion: GT and SUB behavioral tables identical."
                if gt_sub_match else "Conclusion: SUB differs from GT — see pattern rows.")
    if ks_max is not None:
        if ks_max < 1e-4:
            return "Conclusion: spike-time distributions match (KS ≈ 0)."
        if ks_max < 0.2:
            return "Conclusion: small timing differences in worst cell."
        return "Conclusion: significant spike-timing mismatch somewhere."
    if vr_max is not None:
        if vr_max < 1e-4:
            return "Conclusion: output spike timing nearly identical."
        if vr_max < 0.05:
            return "Conclusion: small timing differences on output."
        return "Conclusion: output spike times differ from GT."
    if rmse is not None:
        if rmse < 0.5:
            return "Conclusion: I/O voltages closely aligned."
        if rmse < 2.0:
            return "Conclusion: moderate Vm differences on I/O."
        return "Conclusion: large I/O voltage mismatch — check Vm Traces."
    if sch_r is not None:
        if sch_r > 0.95:
            return "Conclusion: output spike shape highly similar."
        if sch_r > 0.7:
            return "Conclusion: partial spike-shape match on output."
        return "Conclusion: output firing shape differs from GT."
    if jaccard is not None:
        if jaccard > 0.8:
            return "Conclusion: influence maps similar (unusual for black-box)."
        if jaccard > 0.3:
            return "Conclusion: partial overlap in Granger edges."
        return "Conclusion: few shared Granger links — expected for black-box SUB."
    if wasserstein is not None:
        if wasserstein < 1e-3:
            return "Conclusion: ISI spacing distributions match."
        if wasserstein < 5.0:
            return "Conclusion: mild ISI rhythm differences."
        return "Conclusion: ISI distributions differ — firing regularity mismatch."
    if msc_r is not None:
        if msc_r > 0.95:
            return "Conclusion: strong correlation at multiple time scales."
        if msc_r > 0.7:
            return "Conclusion: moderate multi-scale match."
        return "Conclusion: weak multi-scale correlation — timing/rate mismatch."
    if raster_diff is not None:
        if raster_diff == 0:
            return "Conclusion: all spikes match between GT and SUB (this view)."
        if raster_diff < 20:
            return f"Conclusion: {raster_diff} spike mismatches — minor timing/count gaps."
        return f"Conclusion: {raster_diff} spike mismatches — check E and inputs."
    if psp_io_mismatch is not None:
        if psp_io_mismatch == 0:
            return "Conclusion: I/O PSP counts match GT."
        return f"Conclusion: {psp_io_mismatch} I/O neuron×pattern PSP rows differ."
    return ""


def _legend_below(y=-0.20, x=0, xanchor="left"):
    return dict(
        orientation="h",
        yanchor="top",
        y=y,
        x=x,
        xanchor=xanchor,
        bgcolor="#161b22",
        bordercolor="#30363d",
        borderwidth=1,
    )


def _title_top(text):
    return dict(text=text, x=0, xanchor="left", y=0.98, yanchor="top")


def apply_title_legend_layout(
    fig,
    title=None,
    *,
    legend_y=-0.20,
    legend_x=0,
    legend_xanchor="left",
    margin_top=58,
    margin_bottom=90,
    margin_left=55,
    margin_right=20,
    **layout_kw,
):
    """Keep chart title and horizontal legend separated (legend below plot area)."""
    layout = dict(
        legend=_legend_below(legend_y, x=legend_x, xanchor=legend_xanchor),
        margin=dict(l=margin_left, r=margin_right, t=margin_top, b=margin_bottom),
    )
    if title is not None:
        layout["title"] = _title_top(title) if isinstance(title, str) else title
    if "margin" in layout_kw:
        layout["margin"] = {**layout["margin"], **layout_kw.pop("margin")}
    fig.update_layout(**layout, **layout_kw)
    return fig


def set_subplot_x_title_centered(fig, text, n_cols, row=1):
    """One shared x-axis title on the middle panel — avoids overlap with a bottom legend."""
    center = max(1, (n_cols + 1) // 2)
    for c in range(1, n_cols + 1):
        fig.update_xaxes(title_text=text if c == center else "", row=row, col=c)


def apply_gt_sub_subplot_layout(
    fig,
    title,
    *,
    n_cols,
    row=1,
    x_title=None,
    y_title=None,
    legend_y=-0.26,
    margin_bottom=110,
    margin_top=58,
    margin_left=40,
    margin_right=10,
    height=340,
    **layout_kw,
):
    """Multi-panel GT/SUB charts: centered legend below, x-title on middle panel only."""
    apply_title_legend_layout(
        fig,
        title,
        legend_y=legend_y,
        legend_x=0.5,
        legend_xanchor="center",
        margin_top=margin_top,
        margin_bottom=margin_bottom,
        margin_left=margin_left,
        margin_right=margin_right,
        height=height,
        **layout_kw,
    )
    if x_title:
        set_subplot_x_title_centered(fig, x_title, n_cols, row=row)
    if y_title:
        fig.update_yaxes(title_text=y_title, row=row, col=1)
    return fig


PLOTLY_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}


def format_pattern_columns(df):
    """Ensure XOR case labels stay two-digit strings (00, 01) in tables."""
    out = df.reset_index(drop=True).copy()
    for col in out.columns:
        if str(col).lower() in ("pattern", "case"):
            out[col] = out[col].map(normalize_pattern)
    return out


def show_table(df):
    """Read-only table without Glide toolbar (no grey icon boxes on hover)."""
    st.table(format_pattern_columns(df))


def show_scroll_table(df, max_height=420):
    """Scrollable table with sticky header (iframe — works in Streamlit)."""
    formatted = format_pattern_columns(df)
    if formatted.empty:
        st.caption("No rows.")
        return
    if isinstance(max_height, str) and max_height.endswith("px"):
        max_h = int(max_height[:-2])
    else:
        max_h = int(max_height)
    row_h = 34
    natural_h = row_h * (len(formatted) + 1) + 14
    iframe_h = min(natural_h, max_h + 10)
    wrap_h = min(natural_h, max_h)
    overflow = "auto" if natural_h > max_h else "visible"
    table_html = formatted.to_html(index=False, escape=True, border=0)
    doc = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
    html, body {{ margin:0; padding:0; background:#0d1117; color:#e6edf3;
        font-family:'IBM Plex Sans',-apple-system,sans-serif; font-size:13px; }}
    .table-scroll-wrap {{
        max-height:{wrap_h}px; overflow:{overflow}; overflow-x:auto;
        border:1px solid #30363d; border-radius:6px; background:#161b22;
    }}
    table {{ width:100%; border-collapse:collapse; }}
    thead th {{
        position:sticky; top:0; z-index:2; background:#21262d !important;
        color:#e6edf3; padding:8px 10px; text-align:left; border-bottom:1px solid #30363d;
        font-weight:600; white-space:nowrap;
    }}
    tbody td {{
        padding:6px 10px; border-bottom:1px solid #21262d; color:#c9d1d9;
        white-space:nowrap;
    }}
    tbody tr:hover td {{ background:#1c2128; }}
    </style></head><body>
    <div class="table-scroll-wrap">{table_html}</div>
    </body></html>"""
    components.html(doc, height=iframe_h, scrolling=False)


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


def _h5_mtime(path: str) -> float:
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0.0


@st.cache_data(show_spinner=False)
def _cached_pdf_report(gt_path: str, sub_path: str, gt_mtime: float, sub_mtime: float) -> bytes:
    return generate_pdf_report(gt_path, sub_path)


SCORE_CACHE_VERSION = 2


@st.cache_data(show_spinner=True)
def _cached_overall_score(
    gt_path: str,
    sub_path: str,
    gt_mtime: float,
    sub_mtime: float,
    cache_version: int = SCORE_CACHE_VERSION,
) -> dict:
    del cache_version  # bust cache when scoring schema changes
    result = compute_overall_score_fn(gt_path, sub_path)
    if "categories" not in result or "metric_subscores" not in result:
        raise RuntimeError("Scoring module returned an outdated payload — update dashboard_scoring.py")
    return result


def render_sidebar_pdf_download(gt_path: str, sub_path: str) -> None:
    """PDF export in the sidebar so it does not overlap Deploy / Rerun."""
    st.markdown(
        '<div style="font-size:0.68rem;color:#8b949e;padding:6px 2px 2px;text-transform:uppercase;letter-spacing:0.07em;">Export</div>',
        unsafe_allow_html=True,
    )
    if generate_pdf_report is None:
        reason = html.escape(PDF_EXPORT_ERROR or "PDF export unavailable")
        st.markdown(
            f'<span class="pdf-sidebar-status" title="{reason}">PDF unavailable</span>',
            unsafe_allow_html=True,
        )
        return
    try:
        pdf_bytes = _cached_pdf_report(
            gt_path,
            sub_path,
            _h5_mtime(gt_path),
            _h5_mtime(sub_path),
        )
        st.session_state.pop("pdf_last_error", None)
        st.download_button(
            "Download PDF",
            data=pdf_bytes,
            file_name=f"XOR_GT_vs_SUB_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            key="download_pdf_report",
            use_container_width=True,
            help="Download summary report with tables and key charts.",
        )
    except Exception as exc:
        err = html.escape(str(exc))
        st.session_state["pdf_last_error"] = str(exc)
        st.markdown(
            f'<span class="pdf-sidebar-status" title="{err}">PDF failed</span>',
            unsafe_allow_html=True,
        )


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
def normalize_pattern(p):
    """XOR case label as two-digit string (00, 01, 10, 11) — avoids Plotly parsing 00 as 0."""
    s = str(p).strip()
    if s.upper().startswith("XOR_"):
        s = s[4:]
    if s.isdigit():
        return s.zfill(2)
    return s


def pivot_by_pattern(df, index_col, value_col, pattern_order, pattern_col="pattern"):
    """Pivot neuron × pattern matrix with columns in trial_map order."""
    work = df.copy()
    work["_pat"] = work[pattern_col].map(normalize_pattern)
    piv = work.pivot(index=index_col, columns="_pat", values=value_col)
    ordered = [normalize_pattern(p) for p in pattern_order]
    labels = [p for p in ordered if p in piv.columns]
    labels += [c for c in piv.columns if c not in labels]
    if not labels:
        labels = ordered
    return piv.reindex(columns=labels).fillna(0), labels


def apply_pattern_heatmap_axes(fig, x_labels, x_title="Pattern"):
    fig.update_xaxes(
        type="category",
        categoryorder="array",
        categoryarray=x_labels,
        title=x_title,
    )


def spike_times_for(spk_df, label, pattern):
    pat = normalize_pattern(pattern)
    mask = (spk_df["label"] == label) & (
        spk_df["pattern"].astype(str).map(normalize_pattern) == pat
    )
    return spk_df.loc[mask, "t_in_trial"].to_numpy()


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

    _metrics_dir = os.path.dirname(os.path.abspath(__file__))
    default_path = os.path.join(_metrics_dir, "groundtruth.h5")
    _default_sub = os.path.join(_metrics_dir, "substitute.h5")
    default_sub_path = _default_sub if os.path.isfile(_default_sub) else default_path
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
        value=default_sub_path,
        key="path_sub_h5",
        help="H5 with submission /data and /spikes_raw. If substitute.h5 exists beside this script, it is used by default (IF black-box SUB from the pipeline).",
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

    render_sidebar_pdf_download(gt_path, sub_path)
    if st.session_state.get("pdf_last_error"):
        st.error(f"PDF export failed:\n\n{st.session_state['pdf_last_error']}")

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
patterns   = [normalize_pattern(p) for p in tmap["case"].unique()]  # 00, 11, 01, 10
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

    if compute_overall_score_fn is None:
        st.warning(f"Overall score unavailable: {SCORING_ERROR}")
    else:
        try:
            with st.spinner("Computing overall emulation score…"):
                _score = _cached_overall_score(
                    gt_path,
                    sub_path,
                    _h5_mtime(gt_path),
                    _h5_mtime(sub_path),
                    SCORE_CACHE_VERSION,
                )
            _overall = float(_score["overall"])
            _categories = _score["categories"]
            _metric_subscores = _score["metric_subscores"]
            _score_color = "#3fb950" if _overall >= 85 else "#ffa657" if _overall >= 60 else "#f85149"
            st.markdown("**Overall emulation score**")
            _sc1, _sc2 = st.columns([1, 2])
            with _sc1:
                st.markdown(
                    f"""
                    <div class="kpi-card" style="text-align:center;padding:20px 16px;">
                        <div class="kpi-label">Overall Score</div>
                        <div class="kpi-value" style="font-size:2.4rem;color:{_score_color};">{_overall:.1f} / 100</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with _sc2:
                st.markdown("**Category score breakdown**")
                show_table(_categories)
            st.markdown("**Metric subscores**")
            show_scroll_table(_metric_subscores, max_height=380)
            if same_h5_file:
                st.caption(
                    "GT and SUB use the same H5 — expect ~100/100 if scoring logic matches self-consistency."
                )
        except Exception as exc:
            st.error(f"Overall score computation failed: {exc}")

    if same_h5_file:
        st.markdown(
            '<div class="info-box">ℹ️ <b>Self-consistency check</b>: GT and SUB use the same H5. '
            "Metrics that compare both should line up; differences usually mean a metric bug.</div>",
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
        show_scroll_table(cfg_show, max_height=380)
    with col2:
        st.markdown("**XOR Truth Table**")
        if truth_raw is not None:
            st.caption(f"Loaded from `network_config.json` — `{truth_json_path}`")
            show_table(pd.DataFrame(truth_raw))
        else:
            tt_df = pd.DataFrame(TRUTH).T.reset_index().rename(columns={"index": "case"})
            st.caption("Built-in XOR truth table (place `network_config.json` beside the H5 to mirror the notebook).")
            show_table(tt_df)

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
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

# ══════════════════════════════════════════════════════════════
# BEHAVIORAL
# ══════════════════════════════════════════════════════════════
elif active == "behavioral":
    st.markdown('<div class="section-title">🎯 Behavioral Accuracy</div>', unsafe_allow_html=True)
    if truth_raw is not None:
        st.caption(f"Truth table from `{truth_json_path}`.")

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
        ps = normalize_pattern(p)
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
    sub_tp_sum = int(df_sub["TP"].sum())
    sub_fn_sum = int(df_sub["FN"].sum())
    sub_tn_sum = int(df_sub["TN"].sum())
    sub_fp_sum = int(df_sub["FP"].sum())
    sub_overall = (sub_tp_sum + sub_tn_sum) / den_all if den_all else 0.0
    _beh_insight = _insight_sub(overall_acc=sub_overall)
    _match_insight = _insight_sub(gt_sub_match=gt_sub_match)
    _fail_pats = df_sub.loc[
        (df_sub["FN"] > 0) | (df_sub["FP"] > 0), "Pattern"
    ].tolist() if len(df_sub) else []
    show_dynamic_result(
        [
            f"SUB accuracy = {sub_overall:.1%} ({sub_tp_sum + sub_tn_sum}/{den_all} trials correct on E).",
            _beh_insight.replace("Conclusion: ", ""),
            f"GT accuracy = {overall:.1%} (reference).",
            (
                f"Failing SUB patterns: {', '.join(_fail_pats)}"
                if _fail_pats
                else "All XOR patterns pass on SUB."
            ),
            _match_insight.replace("Conclusion: ", ""),
        ],
        verdict=_verdict_from_acc(sub_overall),
    )
    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card"><div class="kpi-label">SUB Accuracy</div>
            <div class="kpi-value">{sub_overall:.1%}</div>
            <div class="kpi-sub">pooled (TP+TN)/N · {_beh_insight}</div></div>
        <div class="kpi-card"><div class="kpi-label">Output Neuron</div>
            <div class="kpi-value" style="font-size:1rem;padding-top:6px">{out_col.replace('_spike','')}</div>
            <div class="kpi-sub">XOR result neuron — primary pass/fail</div></div>
        <div class="kpi-card"><div class="kpi-label">Status</div>
            <div style="margin-top:8px">{badge}</div>
            <div class="kpi-sub">{_match_insight}</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**GT vs SUB Summary**")
    col_t, col_c = st.columns([1, 1])
    with col_t:
        st.markdown("**GT Summary**")
        show_table(df_gt)
    with col_c:
        st.markdown("**SUB Summary**")
        show_table(df_sub)

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
    apply_title_legend_layout(
        fig,
        legend_y=-0.16,
        legend_x=0.5,
        legend_xanchor="center",
        margin_top=52,
        margin_bottom=90,
        barmode="group",
        height=400,
    )
    fig.update_yaxes(range=[0, 1.25])
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

# ══════════════════════════════════════════════════════════════
# VM TRACES  (Stitched + Median ± IQR — matches PDF exactly)
# ══════════════════════════════════════════════════════════════
elif active == "vm_traces":
    st.markdown('<div class="section-title">⚡ Membrane Potential Traces</div>', unsafe_allow_html=True)

    active_vm = get_vm_cols(cfg, scope="active")
    neuron_names = [c.replace("_vm","") for c in active_vm]

    c1, c2, c3 = st.columns([2,2,2])
    _io_vm = [n for n in neuron_names if n in ("PyrIn_A", "PyrIn_B1", "PyrIn_B2", "E")]
    sel_neuron_vm = c1.selectbox(
        "Neuron", neuron_names,
        index=neuron_names.index(_io_vm[0]) if _io_vm and _io_vm[0] in neuron_names else 0,
        key="vm_neuron",
        help="Compare I/O neurons first (PyrIn_A, PyrIn_B1, PyrIn_B2, E). Interneurons may be flat in SUB.",
    )
    sel_pat_vm = c2.selectbox("Pattern", patterns, key="vm_pat", help="XOR input pattern: 00, 01, 10, 11.")
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
                       fill="toself", fillcolor=_hex_rgba(color, 0.2),
                       line=dict(color="rgba(0,0,0,0)"),
                       name=f"{name_prefix} IQR", showlegend=True,
                       hoverinfo="skip"),
            go.Scatter(x=t_ax, y=med.tolist(),
                       mode="lines", line=dict(color=color,width=2),
                       name=f"{name_prefix} median",
                       hovertemplate="t=%{x} ms<br>median=%{y:.3f} mV<extra></extra>"),
        ]

    _vm_gt = stitch(gt_trials, col_vm)
    _vm_sub = stitch(sub_trials, col_vm)
    if _vm_gt.size and _vm_sub.size:
        _n_vm = min(len(_vm_gt), len(_vm_sub))
        _vm_rms = float(np.sqrt(np.mean((_vm_gt[:_n_vm] - _vm_sub[:_n_vm]) ** 2)))
        _vm_ins = _insight_sub(rmse=_vm_rms)
        show_metric_panel(
            "vm_traces",
            [
                f"Neuron {sel_neuron_vm}, pattern {sel_pat_vm}, view {view_type}.",
                f"Stitched Vm RMS(GT−SUB) = {_vm_rms:.4f} mV over {_n_vm} samples.",
                _vm_ins.replace("Conclusion: ", ""),
                (
                    "Mapped I/O neuron — mismatch here matters for black-box SUB."
                    if sel_neuron_vm in ("PyrIn_A", "PyrIn_B1", "PyrIn_B2", "E")
                    else "Interneuron — flat SUB trace may be expected."
                ),
            ],
            verdict="ok" if _vm_rms < 0.5 else "warn" if _vm_rms < 2.0 else "warn",
        )
    else:
        show_metric_panel("vm_traces")

    if view_type in ("Stitched + Median","Both"):
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=[
                f"{sel_neuron_vm} — GT Stitched (pattern {sel_pat_vm}) with Median",
                f"{sel_neuron_vm} — SUB Stitched (pattern {sel_pat_vm}) with Median",
            ],
            shared_xaxes=True,
            shared_yaxes=True,
            vertical_spacing=0.12,
        )
        gt_tr, gt_sep = stitched_median(gt_trials, col_vm, PAL_GT, "GT")
        sb_tr, sb_sep = stitched_median(sub_trials, col_vm, PAL_SUB, "SUB")
        for tr in gt_tr: fig.add_trace(tr, row=1, col=1)
        for tr in sb_tr: fig.add_trace(tr, row=2, col=1)
        for s in gt_sep: fig.add_shape(**s, row=1, col=1)
        for s in sb_sep: fig.add_shape(**s, row=2, col=1)
        apply_dark(fig)
        fig.update_yaxes(title_text="Vm (mV)")
        apply_title_legend_layout(
            fig,
            legend_y=-0.12,
            legend_x=0.5,
            legend_xanchor="center",
            margin_top=52,
            margin_bottom=95,
            height=560,
            hovermode="x unified",
        )
        fig.update_xaxes(title_text="Sample (ms)", row=2, col=1)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

    if view_type in ("Median ± IQR","Both"):
        fig2 = make_subplots(
            rows=1, cols=2,
            subplot_titles=[
                f"{sel_neuron_vm} — Median ± IQR (GT) — Pattern {sel_pat_vm}",
                f"{sel_neuron_vm} — Median ± IQR (SUB) — Pattern {sel_pat_vm}",
            ],
            shared_xaxes=True,
            shared_yaxes=True,
        )
        for tr in median_iqr_trace(gt_trials, col_vm, PAL_GT, "GT"):
            fig2.add_trace(tr, row=1, col=1)
        for tr in median_iqr_trace(sub_trials, col_vm, PAL_SUB, "SUB"):
            fig2.add_trace(tr, row=1, col=2)
        apply_dark(fig2)
        fig2.update_yaxes(title_text="Vm (mV)")
        apply_gt_sub_subplot_layout(
            fig2,
            title=None,
            n_cols=2,
            x_title="Time within trial (ms)",
            height=400,
            hovermode="x unified",
        )
        st.plotly_chart(fig2, use_container_width=True, config=PLOTLY_CONFIG)

# ══════════════════════════════════════════════════════════════
# RASTER
# ══════════════════════════════════════════════════════════════
elif active == "raster":
    st.markdown('<div class="section-title">🔬 Raster Plot</div>', unsafe_allow_html=True)

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
                    mode="markers", marker=dict(symbol="line-ns", size=10, color=PAL_AUTO,
                        line=dict(color=PAL_AUTO, width=1.2)),
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

    out_sp = _out_spike_col(cfg, gt_data)
    e_diff = 0
    if out_sp in gt_f.columns and out_sp in sub_f.columns:
        e_gt = np.where(gt_f[out_sp].to_numpy(int) == 1)[0]
        e_sub = np.where(sub_f[out_sp].to_numpy(int) == 1)[0]
        e_diff = len(np.setxor1d(e_gt, e_sub))
    io_diff = 0
    for _ioc in _io_spike_cols(spike_cols):
        if _ioc in gt_f.columns and _ioc in sub_f.columns:
            io_diff += len(np.setxor1d(
                np.where(gt_f[_ioc].to_numpy(int) == 1)[0],
                np.where(sub_f[_ioc].to_numpy(int) == 1)[0],
            ))
    show_dynamic_result(
        [
            f"Filter: pattern {filter_pat} · view: {view_mode}.",
            f"Total spike mismatches (all neurons): {total_diff}.",
            f"Output {out_sp.replace('_spike', '')} mismatches: {e_diff}.",
            f"I/O neurons (PyrIn_A, B1, B2, E) mismatches: {io_diff}.",
            _insight_sub(raster_diff=total_diff).replace("Conclusion: ", ""),
        ],
        verdict="ok" if e_diff == 0 and total_diff < 50 else "warn",
    )

    apply_dark(fig)
    apply_title_legend_layout(
        fig,
        title=("Raster — GT (blue) vs SUB (orange)" if view_mode == "GT vs SUB overlay"
               else f"Differences Only (GT ⊕ SUB) — {total_diff} differing spikes"),
        legend_y=-0.14,
        legend_x=0.5,
        legend_xanchor="center",
        margin_top=58,
        margin_bottom=88,
        height=max(390, len(spike_cols) * 55 + 110),
        yaxis=dict(tickmode="array", tickvals=list(range(len(spike_cols))),
                   ticktext=[c.replace("_spike", "") for c in spike_cols]),
        xaxis_title="Sample index (ms)",
        hovermode="closest",
    )
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

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
    show_metric_guide("psth")
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
            line=dict(color=PAL_SUB, width=2), name="SUB" if j==0 else None,
            showlegend=(j==0),
            hovertemplate=f"Pattern {p}<br>bin=%{{x}}<br>SUB=%{{y:.3f}}<extra></extra>"),
            row=1, col=j+1)
        fig.add_trace(go.Scatter(
            x=t_ax, y=gt_h[:L].tolist(), mode="lines",
            line=dict(color=PAL_GT, width=2.5, dash="dot"), name="GT" if j==0 else None,
            showlegend=(j==0),
            hovertemplate=f"Pattern {p}<br>bin=%{{x}}<br>GT=%{{y:.3f}}<extra></extra>"),
            row=1, col=j+1)

    apply_dark(fig)
    apply_gt_sub_subplot_layout(
        fig,
        title=f"PSTH — {sel_psth_neuron} (bin={BIN_MS} ms)",
        n_cols=len(patterns),
        x_title="bin",
        y_title="spikes/bin",
        height=380,
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

    if summary_rows:
        _psth_rs = [r["Pearson r"] for r in summary_rows if r.get("Pearson r") is not None]
        _psth_mean_r = float(np.mean(_psth_rs)) if _psth_rs else None
        _worst_psth = min(
            (r for r in summary_rows if r.get("Pearson r") is not None),
            key=lambda r: r["Pearson r"],
            default=None,
        )
        _psth_lines = [f"Neuron {sel_psth_neuron}, bin = {BIN_MS} ms."]
        if _psth_mean_r is not None:
            _psth_lines.append(f"Mean Pearson r across patterns = {_psth_mean_r:.4f}.")
        if _worst_psth:
            _psth_lines.append(
                f"Weakest pattern {_worst_psth['pattern']}: r = {_worst_psth['Pearson r']:.4f}, "
                f"RMSE = {_worst_psth.get('RMSE', '—')}."
            )
        _psth_lines.append(
            "GT and SUB fire on similar schedule."
            if _psth_mean_r and _psth_mean_r > 0.85
            else "Timing or rate differs — check raster/KS even if XOR passes."
        )
        show_metric_panel(
            "psth",
            _psth_lines,
            verdict="ok" if _psth_mean_r and _psth_mean_r > 0.85 else "warn",
        )

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
                line=dict(color=PAL_SUB, width=1.8), name="SUB" if j==0 else None,
                showlegend=(j==0),
                hovertemplate=f"bin=%{{x}}<br>SUB=%{{y:.3f}}<extra></extra>"), row=1, col=j+1)
            row_figs.add_trace(go.Scatter(x=t_ax, y=gt_h[:L].tolist(), mode="lines",
                line=dict(color=PAL_GT, width=2.2, dash="dot"), name="GT" if j==0 else None, showlegend=(j==0),
                hovertemplate=f"bin=%{{x}}<br>GT=%{{y:.3f}}<extra></extra>"), row=1, col=j+1)
        apply_dark(row_figs)
        apply_gt_sub_subplot_layout(
            row_figs,
            title=f"PSTH — {n_name} (bin={BIN_MS} ms)",
            n_cols=len(patterns),
            x_title="bin",
            y_title="spikes/bin",
            height=320,
            hovermode="x unified",
        )
        st.plotly_chart(row_figs, use_container_width=True, config=PLOTLY_CONFIG)

    if summary_rows:
        st.markdown("**PSTH Summary Table**")
        show_table(pd.DataFrame(summary_rows))

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
            # sub first, then GT on top (dotted blue over solid orange when identical)
            rows_sb = []
            for tid in ids:
                t_df2 = get_trial(sub_data, tid)
                if col_ra not in t_df2.columns: continue
                vec2 = t_df2[col_ra].to_numpy(int)[:trial_len]
                rows_sb.append(vec2)
            if rows_sb:
                psth_sb = np.nanmean(np.stack([v[:L_ra] for v in rows_sb[:len(rows_ra)]]),0)
                fig_ra.add_trace(go.Scatter(x=t_ra, y=psth_sb[:L_ra].tolist(), mode="lines",
                    line=dict(color=PAL_SUB, width=2), name="SUB" if j==0 else None,
                    showlegend=(j==0),
                    hovertemplate=f"t=%{{x}} ms<br>rate=%{{y:.3f}}<extra></extra>"), row=1, col=j+1)
            fig_ra.add_trace(go.Scatter(x=t_ra, y=psth_ra.tolist(), mode="lines",
                line=dict(color=PAL_GT, width=2.5, dash="dot"), name="GT" if j==0 else None,
                showlegend=(j==0),
                hovertemplate=f"t=%{{x}} ms<br>rate=%{{y:.3f}}<extra></extra>"), row=1, col=j+1)

        if has_data:
            apply_dark(fig_ra)
            apply_gt_sub_subplot_layout(
                fig_ra,
                title=f"Response-aligned PSTH — {n_name_ra} (0 = earliest input)",
                n_cols=len(resp_patterns),
                x_title="ms rel. to input",
                y_title="spikes/sample",
                height=360,
                hovermode="x unified",
            )
            st.plotly_chart(fig_ra, use_container_width=True, config=PLOTLY_CONFIG)

# ══════════════════════════════════════════════════════════════
# ISI
# ══════════════════════════════════════════════════════════════
elif active == "isi":
    st.markdown('<div class="section-title">⏱ ISI & Fano Factor</div>', unsafe_allow_html=True)
    show_metric_guide("isi")

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
            marker_color=PAL_GT, name="GT",
            text=[f"{v:.3f}" if v is not None and not np.isnan(v) else "—" for v in vals],
            textposition="outside",
            hovertemplate=f"%{{x}}<br>GT {title_r}=%{{y:.4f}}<extra></extra>",
            legendgroup="gt",
            showlegend=(col_r == 1),
        ), row=1, col=col_r)
    if not same_h5_file:
        for vals, col_r, title_r in [(sub_cv, 1, "ISI CV"), (sub_fano, 2, "Fano")]:
            fig_cv.add_trace(go.Bar(
                x=list(neurons_isi), y=vals,
                marker_color=PAL_SUB, name="SUB",
                text=[f"{v:.3f}" if v is not None and not np.isnan(v) else "—" for v in vals],
                textposition="outside",
                hovertemplate=f"%{{x}}<br>SUB {title_r}=%{{y:.4f}}<extra></extra>",
                legendgroup="sub",
                showlegend=(col_r == 1),
            ), row=1, col=col_r)
    apply_dark(fig_cv)
    apply_title_legend_layout(
        fig_cv,
        legend_y=-0.16,
        legend_x=0.5,
        legend_xanchor="center",
        margin_top=52,
        margin_bottom=90,
        height=400,
        hovermode="x",
        barmode="group" if not same_h5_file else "relative",
    )
    fig_cv.update_xaxes(tickangle=30)
    st.plotly_chart(fig_cv, use_container_width=True, config=PLOTLY_CONFIG)

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

        _w_ins = _insight_sub(wasserstein=w_val) if w_val is not None else ""
        show_metric_panel(
            "isi",
            [
                f"Neuron {sel_isi_n}, pattern {sel_isi_p}.",
                f"CV: GT={cv_val:.4f}" + (f", SUB={cv_sub:.4f}" if cv_sub is not None else "") if cv_val is not None else "",
                f"Fano: GT={fano_val:.4f}" + (f", SUB={fano_sub:.4f}" if fano_sub is not None else "") if fano_val is not None else "",
                (
                    f"Wasserstein(ISI) = {w_val:.4f} — {_w_ins.replace('Conclusion: ', '')}"
                    if w_val is not None
                    else "Wasserstein: not enough ISIs in GT and SUB."
                ),
            ],
            verdict="ok" if w_val is not None and w_val < 1.0 else "warn",
        )
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
                <div class="kpi-sub">{_w_ins or ("✓ ≈ 0 (same file)" if same_h5_file and w_val is not None and w_val < 1e-6 else "")}</div></div>
        </div>
        """, unsafe_allow_html=True)

        if len(isi_arr_gt) > 0 or len(isi_arr_sub) > 0:
            fig_isi = go.Figure()
            _add_gt_sub_histogram(fig_isi, isi_arr_gt, isi_arr_sub, n_bins=20)
            apply_dark(fig_isi)
            apply_title_legend_layout(
                fig_isi,
                title=f"{sel_isi_n} : ISI Distribution (Pattern {sel_isi_p})",
                legend_y=-0.24,
                legend_x=0.5,
                legend_xanchor="center",
                margin_top=58,
                margin_bottom=95,
                barmode="group",
                height=380,
                xaxis_title="ISI (ms)",
                yaxis_title="Count",
                hovermode="x unified",
            )
            st.plotly_chart(fig_isi, use_container_width=True, config=PLOTLY_CONFIG)
        else:
            st.info("No spikes for this neuron/pattern.")

# ══════════════════════════════════════════════════════════════
# KS
# ══════════════════════════════════════════════════════════════
elif active == "ks":
    st.markdown('<div class="section-title">📉 KS Test — Spike Time Distributions</div>', unsafe_allow_html=True)
    show_metric_guide("ks")

    try:
        from scipy.stats import ks_2samp
    except ImportError:
        st.error("scipy required for KS test."); st.stop()

    ks_rows = []
    for col in spike_cols:
        lbl = col.replace("_spike","")
        for p in patterns:
            gt_t = spike_times_for(gt_spikes, lbl, p)
            sub_t = spike_times_for(sub_spikes, lbl, p)
            if len(gt_t)>0 and len(sub_t)>0:
                ks, pv = ks_2samp(gt_t, sub_t)
            else:
                ks, pv = None, None
            ks_rows.append({"neuron":col,"pattern":normalize_pattern(p),
                             "gt_spikes":len(gt_t),"sub_spikes":len(sub_t),
                             "ks_stat":round(ks,4) if ks is not None else None,
                             "p_value":round(pv,4) if pv is not None else None})
    ks_df = pd.DataFrame(ks_rows)
    valid = ks_df["ks_stat"].dropna()
    ks_max_val = float(valid.max()) if len(valid) else 0.0
    ks_ok = ks_max_val < 1e-6
    ks_badge = (
        '<span class="badge-ok">✓ KS = 0</span>'
        if ks_ok
        else f'<span class="badge-warn">✗ max KS = {ks_max_val:.4f}</span>'
    )

    _ks_insight = _insight_sub(ks_max=ks_max_val)
    _worst_ks = None
    if len(valid):
        _worst_ks = ks_df.loc[ks_df["ks_stat"].idxmax()]
    _ks_io = ks_df[ks_df["neuron"].isin(_io_spike_cols(spike_cols))]["ks_stat"].dropna()
    _ks_io_max = float(_ks_io.max()) if len(_ks_io) else None
    show_dynamic_result(
        [
            f"Max KS over all neuron×pattern = {ks_max_val:.4f}.",
            (
                f"Worst cell: {_worst_ks['neuron']} @ pattern {_worst_ks['pattern']} "
                f"(KS={_worst_ks['ks_stat']:.4f}, p={_worst_ks['p_value']})."
                if _worst_ks is not None else "No valid KS pairs."
            ),
            (
                f"Max KS on I/O neurons only = {_ks_io_max:.4f}."
                if _ks_io_max is not None else ""
            ),
            _ks_insight.replace("Conclusion: ", ""),
        ],
        verdict="ok" if ks_max_val < 0.2 else "warn",
    )
    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card"><div class="kpi-label">Max KS stat</div>
            <div class="kpi-value">{ks_max_val:.4f}</div>
            <div class="kpi-sub">0 = identical distributions · {_ks_insight}</div></div>
        <div class="kpi-card"><div class="kpi-label">Status</div>
            <div style="margin-top:8px">{ks_badge}</div>
            <div class="kpi-sub">Focus heatmap on E_spike and input rows</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Heatmap KS stat: neuron × pattern
    piv, pat_labels = pivot_by_pattern(ks_df, "neuron", "ks_stat", patterns)
    fig_heat = go.Figure(go.Heatmap(
        z=piv.values.tolist(), x=pat_labels, y=list(piv.index),
        colorscale="YlOrRd", hovertemplate="Neuron=%{y}<br>Pattern=%{x}<br>KS=%{z:.4f}<extra></extra>",
        text=[[f"{v:.4f}" for v in row] for row in piv.values],
        texttemplate="%{text}",
    ))
    apply_dark(fig_heat)
    apply_pattern_heatmap_axes(fig_heat, pat_labels)
    fig_heat.update_layout(
        height=360,
        title=_title_top("KS Statistic — neuron × pattern (0 = perfect)"),
        margin=dict(l=55, r=20, t=58, b=50),
    )
    st.plotly_chart(fig_heat, use_container_width=True, config=PLOTLY_CONFIG)

    # ECDF viewer
    st.markdown("**ECDF Viewer**")
    c1, c2 = st.columns(2)
    sel_ks_n = c1.selectbox("Neuron", spike_cols, key="ks_n")
    sel_ks_p = c2.selectbox("Pattern", patterns, key="ks_p")
    lbl2 = sel_ks_n.replace("_spike","")
    gt_t2 = spike_times_for(gt_spikes, lbl2, sel_ks_p)
    sub_t2 = spike_times_for(sub_spikes, lbl2, sel_ks_p)

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
    apply_title_legend_layout(
        fig_ecdf,
        title=f"{sel_ks_n} — ECDF (pattern {sel_ks_p})",
        legend_y=-0.24,
        legend_x=0.5,
        legend_xanchor="center",
        margin_top=58,
        margin_bottom=95,
        height=380,
        xaxis_title="t_in_trial (ms)",
        yaxis_title="Cumulative fraction of spikes",
        hovermode="x unified",
    )
    st.plotly_chart(fig_ecdf, use_container_width=True, config=PLOTLY_CONFIG)

    st.markdown("**Full KS Table**")
    show_scroll_table(ks_df, max_height=420)

# ══════════════════════════════════════════════════════════════
# PSP COUNTS (in_domain_metrics.ipynb — peak detection on Vm)
# ══════════════════════════════════════════════════════════════
elif active == "psp_counts":
    st.markdown('<div class="section-title">🔺 PSP Counts — Peak Detection (Vm)</div>', unsafe_allow_html=True)
    show_metric_guide("psp_counts")
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
    _psp_io = psp_df[
        psp_df["neuron"].astype(str).isin(("PyrIn_A", "PyrIn_B1", "PyrIn_B2", "E"))
    ] if not psp_df.empty else psp_df
    _psp_io_mm = 0
    if not _psp_io.empty:
        _psp_io_mm = int(
            ((_psp_io["EPSP_GT"] != _psp_io["EPSP_SUB"]) | (_psp_io["IPSP_GT"] != _psp_io["IPSP_SUB"])).sum()
        )
    show_dynamic_result(
        [
            f"Rows compared: {len(psp_df)} (pattern × neuron).",
            "All EPSP/IPSP counts match GT." if match_psp else "Some EPSP/IPSP counts differ from GT.",
            _insight_sub(psp_io_mismatch=_psp_io_mm).replace("Conclusion: ", ""),
        ],
        verdict="ok" if match_psp else "warn",
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
    show_scroll_table(psp_df, max_height=420)

    def _psp_heatmap(piv, pat_labels, title, colorscale, hover_label):
        fig_h = go.Figure(
            go.Heatmap(
                z=piv.values.tolist(),
                x=pat_labels,
                y=piv.index.tolist(),
                colorscale=colorscale,
                hovertemplate=f"Neuron=%{{y}}<br>Pattern=%{{x}}<br>{hover_label}=%{{z}}<extra></extra>",
            )
        )
        apply_dark(fig_h)
        apply_pattern_heatmap_axes(fig_h, pat_labels)
        fig_h.update_layout(
            height=360,
            title=_title_top(title),
            margin=dict(l=55, r=20, t=58, b=50),
        )
        return fig_h

    if not psp_df.empty:
        st.markdown("**EPSP counts heatmaps (GT vs SUB)**")
        piv_epsp_gt, pat_labels = pivot_by_pattern(psp_df, "neuron", "EPSP_GT", patterns)
        piv_epsp_sub, _ = pivot_by_pattern(psp_df, "neuron", "EPSP_SUB", patterns)
        piv_epsp_sub = piv_epsp_sub.reindex(index=piv_epsp_gt.index, fill_value=0)
        _hc1, _hc2 = st.columns(2)
        with _hc1:
            st.plotly_chart(
                _psp_heatmap(piv_epsp_gt, pat_labels, "EPSP counts (GT) — neuron × pattern", "Blues", "EPSP_GT"),
                use_container_width=True,
                config=PLOTLY_CONFIG,
            )
        with _hc2:
            st.plotly_chart(
                _psp_heatmap(piv_epsp_sub, pat_labels, "EPSP counts (SUB) — neuron × pattern", "Oranges", "EPSP_SUB"),
                use_container_width=True,
                config=PLOTLY_CONFIG,
            )

        st.markdown("**IPSP counts heatmaps (GT vs SUB)**")
        piv_ipsp_gt, _ = pivot_by_pattern(psp_df, "neuron", "IPSP_GT", patterns)
        piv_ipsp_sub, _ = pivot_by_pattern(psp_df, "neuron", "IPSP_SUB", patterns)
        piv_ipsp_sub = piv_ipsp_sub.reindex(index=piv_ipsp_gt.index, fill_value=0)
        _hi1, _hi2 = st.columns(2)
        with _hi1:
            st.plotly_chart(
                _psp_heatmap(piv_ipsp_gt, pat_labels, "IPSP counts (GT) — neuron × pattern", "Blues", "IPSP_GT"),
                use_container_width=True,
                config=PLOTLY_CONFIG,
            )
        with _hi2:
            st.plotly_chart(
                _psp_heatmap(piv_ipsp_sub, pat_labels, "IPSP counts (SUB) — neuron × pattern", "Oranges", "IPSP_SUB"),
                use_container_width=True,
                config=PLOTLY_CONFIG,
            )

# ══════════════════════════════════════════════════════════════
# VAN ROSSUM
# ══════════════════════════════════════════════════════════════
elif active == "van_rossum":
    st.markdown('<div class="section-title">🌊 Van Rossum Distance</div>', unsafe_allow_html=True)
    show_metric_guide("van_rossum")

    tau_ms = st.slider("τ (ms)", 5, 100, 20, key="vr_tau_sl", help="Time constant τ: smaller = stricter spike timing match.")

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
                records.append({"pattern": normalize_pattern(p), "trial_id": tid, "neuron": neuron,
                                 "VR": vr_dist(tx, ty, tau_ms), "GT_spikes": tx.size, "SUB_spikes": ty.size})

    vr_df = pd.DataFrame(records)
    vr_pat = (
        vr_df.groupby("pattern")["VR"]
        .agg(["mean", "median", "max"])
        .reindex(patterns)
        .reset_index()
    )
    vr_pat.columns = ["pattern", "VR_mean", "VR_median", "VR_max"]

    max_vr = float(vr_df["VR"].max()) if len(vr_df) else 0.0
    vr_ok = max_vr < 1e-6
    vr_badge = (
        '<span class="badge-ok">✓ VR = 0</span>'
        if vr_ok
        else f'<span class="badge-warn">✗ max VR = {max_vr:.6f}</span>'
    )
    _vr_insight = _insight_sub(vr_max=max_vr)
    _out_sp_vr = _out_spike_col(cfg, gt_data)
    _vr_e = float(vr_df.loc[vr_df["neuron"] == _out_sp_vr, "VR"].max()) if len(vr_df) else max_vr
    _vr_e_ins = _insight_sub(vr_max=_vr_e)
    _worst_vr = vr_df.loc[vr_df["VR"].idxmax()] if len(vr_df) else None
    show_dynamic_result(
        [
            f"τ = {tau_ms} ms · max VR (all neurons) = {max_vr:.6f}.",
            f"Output {_out_sp_vr.replace('_spike', '')} max VR = {_vr_e:.6f} — {_vr_e_ins.replace('Conclusion: ', '')}",
            (
                f"Global worst: {_worst_vr['neuron']} pattern {_worst_vr['pattern']} VR={_worst_vr['VR']:.6f}."
                if _worst_vr is not None else ""
            ),
        ],
        verdict="ok" if _vr_e < 0.05 else "warn",
    )
    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card"><div class="kpi-label">Max VR Distance</div>
            <div class="kpi-value">{max_vr:.6f}</div>
            <div class="kpi-sub">0 = identical · {_vr_insight}</div></div>
        <div class="kpi-card"><div class="kpi-label">τ used</div>
            <div class="kpi-value">{tau_ms} ms</div>
            <div class="kpi-sub">Check E_spike row in heatmap first</div></div>
        <div class="kpi-card"><div class="kpi-label">Status</div>
            <div style="margin-top:8px">{vr_badge}</div></div>
    </div>
    """, unsafe_allow_html=True)

    vr_mean = vr_df.groupby(["neuron", "pattern"])["VR"].mean().reset_index()
    piv, pat_labels = pivot_by_pattern(vr_mean, "neuron", "VR", patterns)
    fig_vr = go.Figure(go.Heatmap(
        z=piv.values.tolist(), x=pat_labels, y=list(piv.index),
        colorscale="YlOrRd",
        hovertemplate="Neuron=%{y}<br>Pattern=%{x}<br>VR=%{z:.6f}<extra></extra>",
        text=[[f"{v:.4f}" for v in row] for row in piv.values],
        texttemplate="%{text}",
    ))
    apply_dark(fig_vr)
    apply_pattern_heatmap_axes(fig_vr, pat_labels)
    fig_vr.update_layout(
        height=360,
        title=_title_top("Van Rossum (mean) — neuron × pattern"),
        margin=dict(l=55, r=20, t=58, b=50),
    )
    st.plotly_chart(fig_vr, use_container_width=True, config=PLOTLY_CONFIG)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**VR by Pattern**")
        show_table(vr_pat.round(6))
    with c2:
        st.markdown("**VR by Neuron**")
        vr_neuron = vr_df.groupby("neuron")["VR"].agg(["mean","median"]).reset_index()
        show_table(vr_neuron.round(6))

# ══════════════════════════════════════════════════════════════
# MULTI-SCALE CORRELATION (in_domain_metrics.ipynb)
# ══════════════════════════════════════════════════════════════
elif active == "msc":
    st.markdown('<div class="section-title">📐 Multi-Scale Correlation</div>', unsafe_allow_html=True)
    show_metric_guide("msc")
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
    _e_msc = _out_spike_col(cfg, gt_data)
    _e_msc_row = neuron_summary[neuron_summary["neuron"] == _e_msc] if not neuron_summary.empty else pd.DataFrame()
    _e_msc_r = float(_e_msc_row["r_mean"].iloc[0]) if len(_e_msc_row) else rmean_all
    show_dynamic_result(
        [
            f"σ range 1–{sigma_max} ms · pooled mean r (patterns) = {rmean_all:.4f}.",
            f"Output {_e_msc.replace('_spike', '')} mean r = {_e_msc_r:.4f}.",
            _insight_sub(msc_r=_e_msc_r).replace("Conclusion: ", ""),
        ],
        verdict="ok" if _e_msc_r > 0.85 else "warn",
    )
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
        show_table(pattern_summary)
    with c_b:
        st.markdown("**Neuron summary**")
        show_table(neuron_summary)

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
                name=neu.replace("_spike", ""),
                line=dict(width=1.8, color=col),
                hovertemplate=f"<b>{neu.replace('_spike', '')}</b><br>σ: %{{x:.0f}} ms<br>Pearson r: %{{y:.4f}}<extra></extra>",
            )
        )
    apply_dark(fig_msc)
    fig_msc.update_layout(
        height=520,
        title=dict(
            text=f"Multi-scale correlation — pattern {sel_msc_pat} (mean over trials)",
            x=0,
            xanchor="left",
            y=0.98,
        ),
        xaxis_title="σ (ms)",
        yaxis_title="Pearson r",
        yaxis=dict(range=[-0.05, 1.05]),
        margin=dict(l=55, r=20, t=70, b=130),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.35,
            x=0,
            xanchor="left",
            bgcolor="#161b22",
            bordercolor="#30363d",
            borderwidth=1,
            font=dict(size=10),
        ),
    )
    st.plotly_chart(fig_msc, use_container_width=True, config=PLOTLY_CONFIG)

# ══════════════════════════════════════════════════════════════
# SCHREIBER
# ══════════════════════════════════════════════════════════════
elif active == "schreiber":
    st.markdown('<div class="section-title">🔗 Schreiber Similarity</div>', unsafe_allow_html=True)
    show_metric_guide("schreiber")

    sigma_ms = st.slider("σ (ms)", 2, 50, 10, key="sch_sig_sl", help="Gaussian blur width: larger σ compares coarser firing envelopes.")

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
    min_r_disp = float(min_r) if not sch_df.empty and not np.isnan(min_r) else float("nan")
    _out_sch = _out_spike_col(cfg, gt_data)
    _e_sch = sch_df[sch_df["neuron"] == _out_sch]["r"].dropna()
    _e_min_sch = float(_e_sch.min()) if len(_e_sch) else min_r_disp
    _sch_ok = not np.isnan(_e_min_sch) and _e_min_sch > 0.95
    _sch_badge = (
        '<span class="badge-ok">✓ r ≈ 1.0 on E</span>'
        if _sch_ok
        else f'<span class="badge-warn">✗ E min r = {_e_min_sch:.4f}</span>'
        if not np.isnan(_e_min_sch)
        else '<span class="badge-warn">no data</span>'
    )
    show_dynamic_result(
        [
            f"σ = {sigma_ms} ms · global min r = {min_r_disp:.4f}" if not np.isnan(min_r_disp) else "No Schreiber pairs computed.",
            (
                f"Output {_out_sch.replace('_spike', '')} min r = {_e_min_sch:.4f} — "
                + _insight_sub(sch_r=_e_min_sch).replace("Conclusion: ", "")
                if not np.isnan(_e_min_sch) else ""
            ),
        ],
        verdict="ok" if _sch_ok else "warn",
    )
    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card"><div class="kpi-label">Min Schreiber r</div>
            <div class="kpi-value">{"—" if np.isnan(min_r_disp) else f"{min_r_disp:.4f}"}</div>
            <div class="kpi-sub">1.0 = identical shape · {_insight_sub(sch_r=_e_min_sch) if not np.isnan(_e_min_sch) else ''}</div></div>
        <div class="kpi-card"><div class="kpi-label">Status</div>
            <div style="margin-top:8px">{_sch_badge}</div></div>
    </div>
    """, unsafe_allow_html=True)

    if not sch_df.empty:
        sch_df["pattern"] = sch_df["pattern"].map(normalize_pattern)
        piv_sch = sch_df.groupby(["neuron", "pattern"])["r"].mean().unstack(fill_value=np.nan)
        pat_labels = [p for p in patterns if p in piv_sch.columns]
        pat_labels += [c for c in piv_sch.columns if c not in pat_labels]
        piv_sch = piv_sch.reindex(columns=pat_labels)
        fig_sch = go.Figure(go.Heatmap(
            z=piv_sch.values.tolist(), x=pat_labels, y=list(piv_sch.index),
            colorscale="RdYlGn", zmin=0, zmax=1,
            hovertemplate="Neuron=%{y}<br>Pattern=%{x}<br>r=%{z:.4f}<extra></extra>",
            text=[[f"{v:.4f}" if not np.isnan(v) else "—" for v in row] for row in piv_sch.values],
            texttemplate="%{text}",
        ))
        apply_dark(fig_sch)
        apply_pattern_heatmap_axes(fig_sch, pat_labels)
        fig_sch.update_layout(
            height=360,
            title=_title_top(f"Schreiber Similarity (mean r, σ={sigma_ms}ms)"),
            margin=dict(l=55, r=20, t=58, b=50),
        )
        st.plotly_chart(fig_sch, use_container_width=True, config=PLOTLY_CONFIG)

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
            st.plotly_chart(fig_sp, use_container_width=True, config=PLOTLY_CONFIG)

# ══════════════════════════════════════════════════════════════
# VM MISMATCH
# ══════════════════════════════════════════════════════════════
elif active == "vm_mismatch":
    st.markdown('<div class="section-title">⚡ Membrane Potential Mismatch (RMS Δ)</div>', unsafe_allow_html=True)
    show_metric_guide("vm_mismatch")

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
    max_rms = float(mm_df["RMS_max"].max()) if len(mm_df) else 0.0
    _rms_ok = max_rms < 1e-6
    _rms_badge = (
        '<span class="badge-ok">✓ RMS ≈ 0</span>'
        if _rms_ok
        else f'<span class="badge-warn">✗ max RMS = {max_rms:.4f} mV</span>'
    )
    _rms_insight = _insight_sub(rmse=max_rms)
    _io_mm = mm_df[mm_df["neuron"].isin(("PyrIn_A", "PyrIn_B1", "PyrIn_B2", "E"))]
    _io_max_rms = float(_io_mm["RMS_max"].max()) if len(_io_mm) else max_rms
    _io_mean_rms = float(_io_mm["RMS_mean"].mean()) if len(_io_mm) else max_rms
    _worst_io = _io_mm.loc[_io_mm["RMS_max"].idxmax()] if len(_io_mm) else None
    show_dynamic_result(
        [
            f"Max RMS Δ (all neurons) = {max_rms:.4f} mV.",
            f"I/O neurons mean RMS = {_io_mean_rms:.4f} mV, max = {_io_max_rms:.4f} mV.",
            (
                f"Worst I/O: {_worst_io['neuron']} max RMS = {_worst_io['RMS_max']:.4f} mV."
                if _worst_io is not None else ""
            ),
            _insight_sub(rmse=_io_max_rms).replace("Conclusion: ", ""),
        ],
        verdict="ok" if _io_max_rms < 0.5 else "warn",
    )
    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card"><div class="kpi-label">Max RMS Δ</div>
            <div class="kpi-value">{max_rms:.4f}</div>
            <div class="kpi-sub">mV · 0 = identical Vm · {_rms_insight}</div></div>
        <div class="kpi-card"><div class="kpi-label">Status</div>
            <div style="margin-top:8px">{_rms_badge}</div>
            <div class="kpi-sub">Interpret PyrIn_A, B1, B2, E — not silent interneurons</div></div>
    </div>
    """, unsafe_allow_html=True)

    fig_mm = go.Figure()
    fig_mm.add_trace(go.Bar(x=mm_df["neuron"], y=mm_df["RMS_mean"],
        name="Mean RMS Δ", marker_color=PAL_VM_MEAN,
        hovertemplate="%{x}<br>Mean RMS=%{y:.6f} mV<extra></extra>"))
    fig_mm.add_trace(go.Bar(x=mm_df["neuron"], y=mm_df["RMS_max"],
        name="Max RMS Δ", marker_color=PAL_VM_MAX,
        hovertemplate="%{x}<br>Max RMS=%{y:.6f} mV<extra></extra>"))
    apply_dark(fig_mm)
    apply_title_legend_layout(
        fig_mm,
        title="Vm Mismatch per Neuron",
        legend_y=-0.24,
        legend_x=0.5,
        legend_xanchor="center",
        margin_top=58,
        margin_bottom=100,
        height=430,
        barmode="group",
        xaxis_title="Neuron",
        yaxis_title="RMS Δ (mV)",
    )
    st.plotly_chart(fig_mm, use_container_width=True, config=PLOTLY_CONFIG)
    show_table(mm_df.round(8))

# ══════════════════════════════════════════════════════════════
# CROSS-CORRELOGRAM
# ══════════════════════════════════════════════════════════════
elif active == "xcorr":
    st.markdown('<div class="section-title">🔀 Cross-Correlogram (CCG)</div>', unsafe_allow_html=True)
    show_metric_guide("xcorr")

    MAX_LAG = st.slider("Max lag (ms)", 5, 50, 15, key="xcorr_lag_sl",
                        help="Lag window in ms for cross-correlation bars in each cell.")
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

    show_dynamic_result(
        [
            f"Pattern {sel_xcorr_pat}, max_lag = {MAX_LAG} ms, showing: {dataset_choice}.",
            "Compare peak positions on I/O cells (E, PyrIn_A, B1, B2) between GT and SUB runs.",
            "Purple diagonal = autocorrelation; blue/orange = cross-correlation.",
            "GT-only peaks on PyrMid/Int without SUB peaks are expected for black-box SUB.",
        ],
        verdict="neutral",
    )

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
                color = PAL_AUTO if i == j else ds_color
                fig_ccg.add_trace(go.Bar(x=lags_list, y=cc.tolist(),
                    marker_color=color, showlegend=False,
                    hovertemplate=f"{labels_short[i]}→{labels_short[j]}<br>lag=%{{x}} ms<br>cc=%{{y:.5f}}<extra></extra>"),
                    row=i+1, col=j+1)

        fig_ccg.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(color=ds_color, size=10), name=f"Cross-corr ({ds_name})",
        ))
        fig_ccg.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(color=PAL_AUTO, size=10), name="Autocorr (diagonal)",
        ))
        apply_dark(fig_ccg)
        cell_sz = max(100, 600 // n_sc)
        apply_title_legend_layout(
            fig_ccg,
            title=f"Cross Correlogram — {ds_name} (Pattern {sel_xcorr_pat}, max_lag={MAX_LAG} ms)",
            legend_y=-0.08,
            legend_x=0.5,
            legend_xanchor="center",
            margin_top=72,
            margin_bottom=110,
            margin_left=80,
            margin_right=20,
            height=cell_sz * n_sc + 140,
            bargap=0,
        )
        for ax in fig_ccg.layout:
            if ax.startswith("xaxis"):
                fig_ccg.layout[ax].update(showticklabels=False, gridcolor="#21262d")
            if ax.startswith("yaxis"):
                fig_ccg.layout[ax].update(showticklabels=False, gridcolor="#21262d")
        st.plotly_chart(fig_ccg, use_container_width=True, config=PLOTLY_CONFIG)

# ══════════════════════════════════════════════════════════════
# GRANGER
# ══════════════════════════════════════════════════════════════
elif active == "granger":
    st.markdown('<div class="section-title">🕸 Granger Causality</div>', unsafe_allow_html=True)
    show_metric_guide("granger")

    try:
        from scipy.stats import f as _f_dist; _HAS_SCIPY=True
    except: _HAS_SCIPY=False

    c1,c2,c3 = st.columns(3)
    gc_bin  = c1.slider("Bin (ms)", 2, 20, 5, key="gc_bin_sl")
    gc_lag  = c2.slider("Lag (bins)", 3, 20, 10, key="gc_lag_sl")
    gc_alpha = c3.select_slider(
        "FDR α",
        options=[0.001, 0.005, 0.01, 0.02, 0.05, 0.10, 0.15, 0.20],
        value=0.05,
        key="gc_a_sl",
        help="False-discovery rate threshold for significant Granger links. Lower = stricter.",
    )
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

    _gc_insight = _insight_sub(jaccard=jacc)
    show_dynamic_result(
        [
            f"Pattern {sel_gc_pat} · bin={gc_bin} ms · lag={gc_lag} · α={gc_alpha}.",
            f"GT edges = {e_gt}, SUB edges = {e_sb}, overlap = {inter}, Jaccard = {jacc:.3f}.",
            _gc_insight.replace("Conclusion: ", ""),
            "Low Jaccard is normal for black-box SUB (different internal neurons).",
        ],
        verdict="ok" if jacc > 0.5 else "warn",
    )
    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card"><div class="kpi-label">GT edges</div><div class="kpi-value">{e_gt}</div>
            <div class="kpi-sub">significant source→target links</div></div>
        <div class="kpi-card"><div class="kpi-label">SUB edges</div><div class="kpi-value">{e_sb}</div>
            <div class="kpi-sub">fewer edges normal for black-box</div></div>
        <div class="kpi-card"><div class="kpi-label">Overlap</div><div class="kpi-value">{inter}</div>
            <div class="kpi-sub">links in both maps</div></div>
        <div class="kpi-card"><div class="kpi-label">Jaccard</div>
            <div class="kpi-value">{jacc:.3f}</div>
            <div class="kpi-sub">{_gc_insight}</div></div>
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
        fig.update_layout(
            height=380,
            title=_title_top(title),
            margin=dict(l=55, r=20, t=58, b=50),
        )
        return fig

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(gc_heatmap(eff_gt, use_gt, f"GT — Pattern {sel_gc_pat}"), use_container_width=True, config=PLOTLY_CONFIG)
    with col2:
        st.plotly_chart(gc_heatmap(eff_sb, use_sb, f"SUB — Pattern {sel_gc_pat}"), use_container_width=True, config=PLOTLY_CONFIG)

    # degree bar
    outdeg = use_sb.sum(0); indeg = use_sb.sum(1)
    fig_deg = go.Figure()
    fig_deg.add_trace(go.Bar(x=labels_gc, y=outdeg.tolist(), name="out-degree", marker_color=PAL_GC_OUT,
        hovertemplate="%{x}<br>out=%{y}<extra></extra>"))
    fig_deg.add_trace(go.Bar(x=labels_gc, y=indeg.tolist(), name="in-degree", marker_color=PAL_GC_IN,
        hovertemplate="%{x}<br>in=%{y}<extra></extra>"))
    apply_dark(fig_deg)
    apply_title_legend_layout(
        fig_deg,
        title=f"Degree (significant @ q≤{gc_alpha}) — SUB, Pattern {sel_gc_pat}",
        legend_y=-0.26,
        legend_x=0.5,
        legend_xanchor="center",
        margin_top=62,
        margin_bottom=100,
        height=380,
        barmode="group",
        xaxis_title="Neuron",
        yaxis_title="Degree",
    )
    st.plotly_chart(fig_deg, use_container_width=True, config=PLOTLY_CONFIG)

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
    show_table(pd.DataFrame(gc_sum_rows))

# ──────────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:3rem;padding:1rem;border-top:1px solid #21262d;
    font-size:0.75rem;color:#8b949e;font-family:'IBM Plex Mono',monospace;">
    XOR Network Metrics Dashboard · GT vs GT · Streamlit
</div>
""", unsafe_allow_html=True)

