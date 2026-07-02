"""
AutoWMS — Shared CSS styles and HTML helper functions.
Call apply_styles() at the top of every page.
"""

import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

/* ── Base ── */
.stApp { background: #0d1117 !important; }
.main .block-container { padding: 1.5rem 2.5rem !important; max-width: 1440px !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #161b22 0%, #0d1117 100%) !important;
    border-right: 1px solid #21262d !important;
}
[data-testid="stSidebar"] * { color: #c9d1d9 !important; }
[data-testid="stSidebar"] a { color: #58a6ff !important; }

/* ── Typography ── */
h1 { font-size:1.9rem !important; font-weight:800 !important; color:#f0f6fc !important; letter-spacing:-.02em; margin-bottom:.25rem !important; }
h2 { font-size:1.3rem !important; font-weight:700 !important; color:#e6edf3 !important; }
h3 { font-size:1.05rem !important; font-weight:600 !important; color:#c9d1d9 !important; }
p, label, span { color:#8b949e !important; }
hr { border:none !important; border-top:1px solid #21262d !important; margin:20px 0 !important; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: linear-gradient(135deg,#161b22,#21262d) !important;
    border: 1px solid #30363d !important;
    border-radius: 14px !important;
    padding: 18px 22px !important;
    transition: border-color .2s;
}
[data-testid="metric-container"]:hover { border-color:#388bfd !important; }
[data-testid="stMetricLabel"] { color:#8b949e !important; font-size:12px !important; text-transform:uppercase; letter-spacing:.06em; }
[data-testid="stMetricValue"] { color:#f0f6fc !important; font-size:2rem !important; font-weight:800 !important; }
[data-testid="stMetricDelta"] { font-size:12px !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { background:transparent !important; border-bottom:1px solid #21262d !important; gap:0 !important; }
.stTabs [data-baseweb="tab"] {
    background:transparent !important; border:none !important; color:#8b949e !important;
    padding:10px 22px !important; font-weight:500 !important; font-size:14px !important;
}
.stTabs [aria-selected="true"] {
    background:transparent !important; color:#f0f6fc !important;
    border-bottom:2px solid #1f6feb !important; font-weight:600 !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius:8px !important; font-weight:600 !important; font-size:13px !important;
    padding:8px 18px !important; border:1px solid #30363d !important;
    transition:all .2s ease !important; color:#c9d1d9 !important;
    background:#21262d !important;
}
.stButton > button:hover { background:#30363d !important; border-color:#8b949e !important; color:#f0f6fc !important; }
button[data-testid="baseButton-primary"],
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg,#1f6feb,#388bfd) !important;
    border-color:#1f6feb !important; color:white !important;
}
button[data-testid="baseButton-primary"]:hover,
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg,#388bfd,#58a6ff) !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stDateInput > div > div > input,
.stTextArea textarea {
    background:#161b22 !important; border:1px solid #30363d !important;
    border-radius:8px !important; color:#e6edf3 !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stDateInput > div > div > input:focus { border-color:#1f6feb !important; box-shadow:0 0 0 3px rgba(31,111,235,.15) !important; }
.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div {
    background:#161b22 !important; border:1px solid #30363d !important;
    border-radius:8px !important; color:#e6edf3 !important;
}
[data-testid="stForm"] {
    background:#161b22 !important; border:1px solid #21262d !important;
    border-radius:14px !important; padding:24px !important;
}

/* ── DataFrames ── */
[data-testid="stDataFrame"] { border-radius:12px !important; overflow:hidden !important; }

/* ── Expander ── */
details summary { background:#161b22 !important; border:1px solid #21262d !important; border-radius:10px !important; color:#e6edf3 !important; }

/* ── Page hero banner ── */
.page-hero {
    background: linear-gradient(135deg,rgba(31,111,235,.12) 0%,rgba(56,139,253,.07) 60%,transparent 100%);
    border: 1px solid rgba(31,111,235,.3);
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 26px;
    position: relative; overflow: hidden;
}
.page-hero::after {
    content:''; position:absolute; top:-60%; right:-5%;
    width:350px; height:350px;
    background: radial-gradient(circle,rgba(31,111,235,.18) 0%,transparent 70%);
    pointer-events:none;
}
.page-hero-icon { font-size:32px; }
.page-hero-title { font-size:26px; font-weight:800; color:#f0f6fc !important; margin:8px 0 4px; }
.page-hero-sub { font-size:14px; color:#8b949e !important; margin:0; }

/* ── Stat / KPI cards ── */
.kpi-wrap { display:flex; flex-direction:column; gap:4px; align-items:center; }
.kpi-num  { font-size:38px; font-weight:800; color:#f0f6fc; line-height:1; }
.kpi-lbl  { font-size:11px; font-weight:600; color:#6e7681; text-transform:uppercase; letter-spacing:.08em; text-align:center; }

/* ── Status badges ── */
.badge { display:inline-flex; align-items:center; gap:5px; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:600; }
.badge::before { content:'●'; font-size:7px; }
.badge-open       { background:rgba(63,185,80,.12);  color:#3fb950; border:1px solid rgba(63,185,80,.3);  }
.badge-partial    { background:rgba(210,153,34,.12); color:#d29922; border:1px solid rgba(210,153,34,.3); }
.badge-closed     { background:rgba(139,148,158,.12);color:#8b949e; border:1px solid rgba(139,148,158,.3);}
.badge-pending    { background:rgba(210,153,34,.12); color:#d29922; border:1px solid rgba(210,153,34,.3); }
.badge-approved   { background:rgba(63,185,80,.12);  color:#3fb950; border:1px solid rgba(63,185,80,.3);  }
.badge-rejected   { background:rgba(248,81,73,.12);  color:#f85149; border:1px solid rgba(248,81,73,.3);  }
.badge-pass       { background:rgba(63,185,80,.12);  color:#3fb950; border:1px solid rgba(63,185,80,.3);  }
.badge-fail       { background:rgba(248,81,73,.12);  color:#f85149; border:1px solid rgba(248,81,73,.3);  }
.badge-dispatched { background:rgba(88,166,255,.12); color:#58a6ff; border:1px solid rgba(88,166,255,.3); }
.badge-picking    { background:rgba(210,153,34,.12); color:#d29922; border:1px solid rgba(210,153,34,.3); }
.badge-packing    { background:rgba(168,94,253,.12); color:#a855f7; border:1px solid rgba(168,94,253,.3); }
.badge-in-stock   { background:rgba(63,185,80,.12);  color:#3fb950; border:1px solid rgba(63,185,80,.3);  }
.badge-low        { background:rgba(210,153,34,.12); color:#d29922; border:1px solid rgba(210,153,34,.3); }
.badge-out        { background:rgba(248,81,73,.12);  color:#f85149; border:1px solid rgba(248,81,73,.3);  }

/* ── Alert boxes ── */
.alert { border-radius:10px; padding:14px 18px; margin:8px 0; font-size:14px; font-weight:500; }
.alert-warn    { background:rgba(210,153,34,.1); border:1px solid rgba(210,153,34,.3); color:#d29922 !important; }
.alert-danger  { background:rgba(248,81,73,.1);  border:1px solid rgba(248,81,73,.3);  color:#f85149 !important; }
.alert-success { background:rgba(63,185,80,.1);  border:1px solid rgba(63,185,80,.3);  color:#3fb950 !important; }
.alert-info    { background:rgba(88,166,255,.1); border:1px solid rgba(88,166,255,.3); color:#58a6ff !important; }

/* ── Info / detail box ── */
.info-box { background:#161b22; border:1px solid #21262d; border-radius:12px; padding:18px 22px; }
.info-row { display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid #21262d; }
.info-row:last-child { border-bottom:none; }
.info-key { font-size:13px; color:#6e7681 !important; }
.info-val { font-size:13px; color:#e6edf3 !important; font-weight:500; text-align:right; }

/* ── Blocked zone ── */
.blocked-zone {
    background:rgba(248,81,73,.05); border:2px dashed rgba(248,81,73,.45);
    border-radius:16px; padding:38px; text-align:center;
}
.blocked-icon  { font-size:52px; margin-bottom:14px; }
.blocked-title { font-size:22px; font-weight:700; color:#f85149 !important; margin:6px 0; }
.blocked-desc  { font-size:14px; color:#8b949e !important; max-width:420px; margin:8px auto 0; line-height:1.65; }

/* ── Workflow steps ── */
.wf-track { display:flex; align-items:center; margin:16px 0 24px; }
.wf-step  { display:flex; flex-direction:column; align-items:center; flex:1; }
.wf-circle {
    width:38px; height:38px; border-radius:50%; display:flex;
    align-items:center; justify-content:center; font-size:15px; font-weight:700; border:2px solid;
}
.wf-line { flex:1; height:2px; margin-bottom:22px; }
.wf-done   .wf-circle { background:#163320; border-color:#3fb950; color:#3fb950; }
.wf-done   .wf-line   { background:#3fb950; }
.wf-active .wf-circle { background:#1c3461; border-color:#58a6ff; color:#58a6ff; }
.wf-active .wf-line   { background:#21262d; }
.wf-todo   .wf-circle { background:#161b22; border-color:#30363d; color:#6e7681; }
.wf-todo   .wf-line   { background:#21262d; }
.wf-lbl { font-size:11px; margin-top:6px; font-weight:500; }
.wf-done   .wf-lbl { color:#3fb950 !important; }
.wf-active .wf-lbl { color:#58a6ff !important; }
.wf-todo   .wf-lbl { color:#6e7681 !important; }

/* ── Sidebar branding ── */
.sb-brand { padding:18px 0 10px; text-align:center; }
.sb-logo  { font-size:38px; }
.sb-name  { font-size:18px; font-weight:800; color:#f0f6fc !important; margin-top:6px; }
.sb-tag   { font-size:10px; color:#6e7681 !important; text-transform:uppercase; letter-spacing:.12em; }

/* ── Movement feed cards ── */
.mv-card { background:#161b22; border:1px solid #21262d; border-radius:10px; padding:12px 16px; margin-bottom:6px; }
.mv-ref  { font-size:11px; color:#6e7681 !important; }
.mv-desc { font-size:13px; color:#e6edf3 !important; font-weight:500; }
.mv-qty-in  { font-size:17px; font-weight:700; color:#3fb950 !important; }
.mv-qty-out { font-size:17px; font-weight:700; color:#f85149 !important; }
.mv-bal  { font-size:11px; color:#6e7681 !important; }

/* ── Empty state ── */
.empty-state { background:#161b22; border:2px dashed #30363d; border-radius:14px; padding:44px; text-align:center; }
.empty-icon  { font-size:40px; margin-bottom:12px; }
.empty-msg   { font-size:15px; font-weight:600; color:#8b949e !important; }
.empty-sub   { font-size:13px; color:#6e7681 !important; margin-top:6px; }

/* ── Footer ── */
.footer { text-align:center; color:#6e7681 !important; font-size:12px; padding:16px 0 8px; border-top:1px solid #21262d; margin-top:32px; }
</style>
"""


def apply_styles():
    st.markdown(_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HTML helpers
# ─────────────────────────────────────────────────────────────────────────────

def badge(status: str) -> str:
    s = status.lower().replace(" ", "-")
    return f'<span class="badge badge-{s}">{status}</span>'


def alert(msg: str, kind: str = "info") -> str:
    icons = {"info": "ℹ️", "warn": "⚠️", "danger": "🚫", "success": "✅"}
    icon = icons.get(kind, "ℹ️")
    return f'<div class="alert alert-{kind}">{icon}&nbsp; {msg}</div>'


def page_hero(icon: str, title: str, subtitle: str):
    st.markdown(f"""
    <div class="page-hero">
        <div class="page-hero-icon">{icon}</div>
        <div class="page-hero-title">{title}</div>
        <p class="page-hero-sub">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def sidebar_brand():
    st.sidebar.markdown("""
    <div class="sb-brand">
        <div class="sb-logo">🏭</div>
        <div class="sb-name">AutoWMS</div>
        <div class="sb-tag">Automotive Spare Parts</div>
    </div>
    <hr style="border-color:#21262d; margin:10px 0 16px;">
    """, unsafe_allow_html=True)


def info_box(rows: list[tuple]) -> str:
    """rows = [(key, value), ...]"""
    inner = "".join(
        f'<div class="info-row"><span class="info-key">{k}</span>'
        f'<span class="info-val">{v}</span></div>'
        for k, v in rows
    )
    return f'<div class="info-box">{inner}</div>'


def workflow_html(steps: list[tuple]) -> str:
    """
    steps = [(label, state), ...]
    state: 'done' | 'active' | 'todo'
    """
    html = '<div class="wf-track">'
    for i, (label, state) in enumerate(steps):
        icons = {"done": "✓", "active": str(i + 1), "todo": str(i + 1)}
        icon = icons.get(state, str(i + 1))
        html += f"""
        <div class="wf-step wf-{state}">
            <div class="wf-circle">{icon}</div>
            <div class="wf-lbl">{label}</div>
        </div>"""
        if i < len(steps) - 1:
            line_state = "done" if state == "done" else "todo"
            html += f'<div class="wf-line wf-{line_state}"></div>'
    html += "</div>"
    return html


def empty_state(icon: str, msg: str, sub: str = "") -> str:
    return f"""
    <div class="empty-state">
        <div class="empty-icon">{icon}</div>
        <div class="empty-msg">{msg}</div>
        <div class="empty-sub">{sub}</div>
    </div>"""
