"""ARS Production Pipeline -- v3

Refined utilitarian dashboard. Like a well-run control room.
Run: streamlit run ui_mockup.py
"""

import streamlit as st
import time
from datetime import datetime

st.set_page_config(
    page_title="CSI Velocity",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── FONTS & THEME ────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400;600;700&family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    #MainMenu, footer, header {visibility: hidden;}

    .stApp {
        background: #faf9f7;
        font-family: 'DM Sans', sans-serif;
    }

    /* ─── SIDEBAR ─── */
    section[data-testid="stSidebar"] {
        background: #1b1b1f;
        border-right: none;
        padding-top: 0;
    }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stMultiSelect label {
        color: #78787e !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 11px !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] .stSelectbox > div > div,
    section[data-testid="stSidebar"] .stMultiSelect > div > div {
        background: #28282e;
        border-color: #38383e;
        color: #e8e8ea;
        font-family: 'DM Sans', sans-serif;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {
        color: #b8b8be !important;
    }

    /* ─── SIDEBAR BRAND ─── */
    .sidebar-brand {
        padding: 28px 24px 20px 24px;
        border-bottom: 1px solid #28282e;
        margin-bottom: 24px;
    }
    .sidebar-brand-name {
        font-family: 'Source Serif 4', serif;
        font-size: 22px;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: 0.5px;
    }
    .sidebar-brand-sub {
        font-family: 'DM Sans', sans-serif;
        font-size: 11px;
        color: #58585e;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-top: 4px;
    }

    /* ─── SIDEBAR SECTION ─── */
    .sidebar-section {
        padding: 0 24px;
        margin-bottom: 20px;
    }
    .sidebar-section-title {
        font-family: 'DM Sans', sans-serif;
        font-size: 10px;
        font-weight: 700;
        color: #48484e;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 10px;
    }

    /* ─── SIDEBAR FILE STATUS ─── */
    .sf-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 6px 0;
    }
    .sf-label {
        font-size: 13px;
        color: #98989e;
    }
    .sf-ok {
        font-size: 11px;
        font-weight: 600;
        color: #34d399;
        font-family: 'JetBrains Mono', monospace;
    }
    .sf-miss {
        font-size: 11px;
        font-weight: 600;
        color: #f87171;
        font-family: 'JetBrains Mono', monospace;
    }

    /* ─── MAIN AREA ─── */
    .main-header {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 32px;
        padding-bottom: 16px;
        border-bottom: 2px solid #e8e6e1;
    }
    .main-title {
        font-family: 'Source Serif 4', serif;
        font-size: 32px;
        font-weight: 700;
        color: #1b1b1f;
    }
    .main-context {
        font-family: 'DM Sans', sans-serif;
        font-size: 14px;
        color: #98989e;
    }

    /* ─── QUEUE ─── */
    .queue-header {
        font-family: 'DM Sans', sans-serif;
        font-size: 11px;
        font-weight: 700;
        color: #78787e;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 16px;
    }

    .queue-card {
        background: #ffffff;
        border: 1px solid #e8e6e1;
        border-radius: 6px;
        padding: 20px 24px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: border-color 0.2s;
    }
    .queue-card:hover {
        border-color: #c8c6c1;
    }
    .queue-card-active {
        border-left: 3px solid #0d9488;
        background: #f0fdfa;
    }
    .queue-card-done {
        border-left: 3px solid #34d399;
        opacity: 0.7;
    }
    .queue-client-name {
        font-family: 'Source Serif 4', serif;
        font-size: 18px;
        font-weight: 600;
        color: #1b1b1f;
    }
    .queue-client-id {
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        color: #98989e;
        margin-left: 8px;
    }
    .queue-meta {
        font-size: 12px;
        color: #98989e;
        margin-top: 3px;
    }
    .queue-status {
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        padding: 4px 12px;
        border-radius: 4px;
    }
    .queue-status-ready {
        color: #0d9488;
        background: #f0fdfa;
        border: 1px solid #99f6e4;
    }
    .queue-status-running {
        color: #d97706;
        background: #fffbeb;
        border: 1px solid #fde68a;
    }
    .queue-status-done {
        color: #16a34a;
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
    }

    /* ─── PRODUCT PILLS ─── */
    .product-row {
        display: flex;
        gap: 8px;
        margin-bottom: 24px;
        flex-wrap: wrap;
    }
    .product-pill {
        font-family: 'DM Sans', sans-serif;
        font-size: 13px;
        font-weight: 600;
        padding: 8px 20px;
        border-radius: 100px;
        border: 1.5px solid #e8e6e1;
        color: #58585e;
        background: #ffffff;
        cursor: pointer;
        transition: all 0.15s;
    }
    .product-pill:hover {
        border-color: #0d9488;
        color: #0d9488;
    }
    .product-pill-active {
        background: #0d9488;
        color: #ffffff;
        border-color: #0d9488;
    }
    .product-pill-count {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        opacity: 0.7;
        margin-left: 4px;
    }

    /* ─── MODULE GRID ─── */
    .mod-group {
        margin-bottom: 20px;
    }
    .mod-group-title {
        font-family: 'DM Sans', sans-serif;
        font-size: 13px;
        font-weight: 700;
        color: #1b1b1f;
        margin-bottom: 6px;
    }
    .mod-group-items {
        font-size: 12px;
        color: #78787e;
        line-height: 1.7;
    }
    .mod-count {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: #0d9488;
        margin-left: 4px;
    }

    /* ─── RUN BAR ─── */
    .run-bar {
        background: #ffffff;
        border: 1px solid #e8e6e1;
        border-radius: 6px;
        padding: 16px 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 24px;
        margin-bottom: 24px;
    }
    .run-bar-info {
        font-size: 14px;
        color: #58585e;
    }
    .run-bar-info strong {
        color: #1b1b1f;
    }
    .run-bar-time {
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        color: #98989e;
    }

    /* ─── OVERRIDE STREAMLIT BUTTONS ─── */
    .stButton > button[kind="primary"] {
        background: #0d9488;
        border: none;
        border-radius: 6px;
        font-family: 'DM Sans', sans-serif;
        font-weight: 600;
        font-size: 14px;
        padding: 10px 28px;
    }
    .stButton > button[kind="primary"]:hover {
        background: #0f766e;
    }
    .stButton > button[kind="secondary"] {
        border-radius: 6px;
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        font-size: 13px;
        border-color: #d8d6d1;
        color: #58585e;
    }

    /* ─── DOWNLOAD GRID ─── */
    .dl-card {
        background: #ffffff;
        border: 1px solid #e8e6e1;
        border-radius: 6px;
        padding: 20px;
        text-align: center;
    }
    .dl-ext {
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        font-weight: 600;
        color: #0d9488;
        background: #f0fdfa;
        padding: 4px 12px;
        border-radius: 4px;
        display: inline-block;
        margin-bottom: 8px;
    }
    .dl-name {
        font-family: 'DM Sans', sans-serif;
        font-size: 14px;
        font-weight: 600;
        color: #1b1b1f;
    }
    .dl-meta {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: #98989e;
        margin-top: 2px;
    }

    /* ─── PROGRESS ─── */
    .stProgress > div > div > div {
        background: #0d9488 !important;
    }
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ──────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-brand-name">Velocity</div>
        <div class="sidebar-brand-sub">Report Pipeline</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section"><div class="sidebar-section-title">Analyst</div></div>', unsafe_allow_html=True)
    csm = st.selectbox("Analyst", ["James Gilmore", "Jordan", "Aaron", "Gregg", "Dan", "Max"],
                        label_visibility="collapsed")

    st.markdown('<div class="sidebar-section"><div class="sidebar-section-title">Period</div></div>', unsafe_allow_html=True)
    month = st.selectbox("Period", ["2026.03", "2026.02", "2026.01", "2025.12"],
                          label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-section">
        <div class="sidebar-section-title">Data Status</div>
        <div class="sf-row"><span class="sf-label">ODD File</span><span class="sf-ok">READY</span></div>
        <div class="sf-row"><span class="sf-label">Transactions</span><span class="sf-ok">13 FILES</span></div>
        <div class="sf-row"><span class="sf-label">Z Accounts</span><span class="sf-ok">2 SNAPS</span></div>
        <div class="sf-row"><span class="sf-label">Config</span><span class="sf-ok">FOUND</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="sidebar-section">
        <div class="sidebar-section-title">Recent Runs</div>
        <div style="font-size: 12px; color: #58585e; line-height: 1.8; font-family: 'JetBrains Mono', monospace;">
            1453 Connex &middot; Feb 26<br>
            1673 Neighborhood &middot; Feb 26<br>
            1200 Guardians &middot; Jan 26<br>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─── MAIN ─────────────────────────────────────────────────────────────

# Mock data
clients = {
    "1200": {"name": "Guardians Credit Union", "accounts": "24,812"},
    "1217": {"name": "Pioneer Federal Credit Union", "accounts": "31,440"},
    "1453": {"name": "Connex Credit Union", "accounts": "18,293"},
    "1673": {"name": "Neighborhood Credit Union", "accounts": "45,614"},
    "1780": {"name": "USF Federal Credit Union", "accounts": "22,359"},
}

# Header
st.markdown(f"""
<div class="main-header">
    <div class="main-title">Generate Reports</div>
    <div class="main-context">{csm} &middot; {month}</div>
</div>
""", unsafe_allow_html=True)

# Client selection
client_options = [f"{cid} - {info['name']}" for cid, info in clients.items()]
selected_clients = st.multiselect(
    "Add clients to queue",
    client_options,
    default=[client_options[0]],
    label_visibility="visible",
)

# Product selection as pills
st.markdown("<br>", unsafe_allow_html=True)
product = st.radio(
    "Product",
    ["ARS Full Suite", "Transaction Analysis", "Deposits", "Custom"],
    horizontal=True,
    label_visibility="collapsed",
)

# Module details
module_groups = {
    "ARS Full Suite": {
        "Overview": {"count": 3, "items": "Stat Codes, Product Codes, Eligibility"},
        "Debit Card Throughput": {"count": 5, "items": "Penetration, Trends, Branches, Funnel, Overlays"},
        "Reg E / Overdraft": {"count": 3, "items": "Opt-in Status, Branch Rates, Dimensions"},
        "Attrition": {"count": 3, "items": "Closure Rates, Demographics, Revenue Impact"},
        "Mailer Campaign": {"count": 5, "items": "Response, Impact, Cohort Lift, Reach, Insights"},
        "Value & Insights": {"count": 3, "items": "Revenue Attribution, Synthesis, Conclusions"},
    },
    "Transaction Analysis": {
        "Portfolio": {"count": 5, "items": "KPIs, Engagement, Demographics, Seasonal, Trends"},
        "Merchant": {"count": 4, "items": "Top Merchants, Concentration, Categories, Trends"},
        "Competition": {"count": 6, "items": "Detection, Wallet Share, Threat, High-Level, Drilldown"},
        "Operations": {"count": 5, "items": "Branch, Transaction Type, Product, Interchange, Payroll"},
        "Risk": {"count": 4, "items": "Attrition, Balance, Retention, Early Warning"},
        "Executive": {"count": 3, "items": "Scorecard, Priorities, Roadmap"},
    },
    "Deposits": {
        "Baseline": {"count": 4, "items": "Portfolio, Tier Analysis, Segmentation, Cross-checks"},
        "Campaign": {"count": 5, "items": "Response Summary, Cohort DID, Segment Analysis"},
        "Lift Analysis": {"count": 4, "items": "Per-Offer, Per-Segment, Distribution, Trajectory"},
        "Presentation": {"count": 2, "items": "Executive Summary, Visuals"},
    },
}

total_modules = 0
if product in module_groups:
    groups = module_groups[product]
    total_modules = sum(g["count"] for g in groups.values())

    with st.expander(f"{total_modules} modules in {product}", expanded=False):
        cols = st.columns(3)
        for i, (group_name, group_info) in enumerate(groups.items()):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="mod-group">
                    <div class="mod-group-title">{group_name}<span class="mod-count">{group_info['count']}</span></div>
                    <div class="mod-group-items">{group_info['items']}</div>
                </div>
                """, unsafe_allow_html=True)

# Queue
if selected_clients:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="queue-header">Queue</div>', unsafe_allow_html=True)

    for sel in selected_clients:
        cid = sel.split(" - ")[0]
        cname = sel.split(" - ")[1]
        accts = clients[cid]["accounts"]
        st.markdown(f"""
        <div class="queue-card">
            <div>
                <div>
                    <span class="queue-client-name">{cname}</span>
                    <span class="queue-client-id">{cid}</span>
                </div>
                <div class="queue-meta">{accts} accounts &middot; {product} &middot; {total_modules} modules</div>
            </div>
            <div class="queue-status queue-status-ready">READY</div>
        </div>
        """, unsafe_allow_html=True)

    # Run bar
    est_time = f"{len(selected_clients) * 15}-{len(selected_clients) * 25} min"
    st.markdown(f"""
    <div class="run-bar">
        <div class="run-bar-info">
            <strong>{len(selected_clients)}</strong> client(s) &middot;
            <strong>{total_modules}</strong> modules each &middot;
            {product}
        </div>
        <div class="run-bar-time">Est. {est_time}</div>
    </div>
    """, unsafe_allow_html=True)

    col_run, col_space = st.columns([1, 3])
    with col_run:
        run_clicked = st.button("Run Pipeline", type="primary", use_container_width=True)

    if run_clicked:
        st.markdown("<br>", unsafe_allow_html=True)

        for sel in selected_clients:
            cid = sel.split(" - ")[0]
            cname = sel.split(" - ")[1]

            st.markdown(f"""
            <div class="queue-card queue-card-active">
                <div>
                    <span class="queue-client-name">{cname}</span>
                    <span class="queue-client-id">{cid}</span>
                </div>
                <div class="queue-status queue-status-running">RUNNING</div>
            </div>
            """, unsafe_allow_html=True)

            progress = st.progress(0, text="Initializing...")
            status = st.status(f"Processing {cname}...", expanded=True)

            steps = [
                ("Loading ODD file", 8),
                ("Validating columns", 12),
                ("Building subsets", 18),
                ("Overview modules", 25),
                ("DCTR analysis", 40),
                ("Reg E analysis", 50),
                ("Attrition analysis", 60),
                ("Mailer campaign analysis", 78),
                ("Value analysis", 83),
                ("Insights synthesis", 88),
                ("Excel workbook", 93),
                ("PowerPoint deck", 97),
                ("Saving outputs", 100),
            ]

            for msg, pct in steps:
                status.write(msg)
                progress.progress(pct, text=f"{msg}")
                time.sleep(0.25)

            status.update(label=f"{cname} complete", state="complete")
            progress.empty()

        # Downloads
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="queue-header">Downloads</div>', unsafe_allow_html=True)

        for sel in selected_clients:
            cid = sel.split(" - ")[0]
            cname = sel.split(" - ")[1]

            st.markdown(f"""
            <div class="queue-card queue-card-done">
                <div>
                    <span class="queue-client-name">{cname}</span>
                    <span class="queue-client-id">{cid}</span>
                </div>
                <div class="queue-status queue-status-done">COMPLETE</div>
            </div>
            """, unsafe_allow_html=True)

            dl1, dl2, dl3 = st.columns(3)
            with dl1:
                st.markdown('<div class="dl-card"><div class="dl-ext">.pptx</div><div class="dl-name">PowerPoint</div><div class="dl-meta">52 slides &middot; 8.4 MB</div></div>', unsafe_allow_html=True)
                st.download_button(f"Download", data=b"mock", file_name=f"{cid}-{cname}-ARS.pptx",
                                  use_container_width=True, type="primary", key=f"dl_pptx_{cid}")
            with dl2:
                st.markdown('<div class="dl-card"><div class="dl-ext">.xlsx</div><div class="dl-name">Excel Workbook</div><div class="dl-meta">22 sheets &middot; 3.1 MB</div></div>', unsafe_allow_html=True)
                st.download_button(f"Download", data=b"mock", file_name=f"{cid}-{cname}-Analysis.xlsx",
                                  use_container_width=True, key=f"dl_xlsx_{cid}")
            with dl3:
                st.markdown('<div class="dl-card"><div class="dl-ext">.zip</div><div class="dl-name">All Outputs</div><div class="dl-meta">Everything &middot; 24 MB</div></div>', unsafe_allow_html=True)
                st.download_button(f"Download", data=b"mock", file_name=f"{cid}-Complete.zip",
                                  use_container_width=True, key=f"dl_zip_{cid}")

            st.markdown("<br>", unsafe_allow_html=True)
