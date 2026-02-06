# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests, io, re, pytz, hashlib
from datetime import datetime, timedelta
from requests.exceptions import RequestException, Timeout

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(page_title="LMCP Hub", page_icon="📌", layout="wide")

UPCOMING_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"
SUBMISSIONS_CSV_URL = "https://docs.google.com/spreadsheets/d/1jB78iGRp3pmwib7k_MfdwzMC402QY9MPtHKC3TAAlPQ/export?format=csv&gid=1864466191"
LOGO_URL = "https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg"

TZ = pytz.timezone("Africa/Johannesburg")
now_dt = datetime.now(TZ)
today = now_dt.date()

VIEW_OPTIONS = ["All", "Next 7 Days", "Term Documents", "Assessment Schedule", "New Updates"]
NEW_UPDATES_DEFAULT_HOURS = 72

# ======================================================
# QUICK SELECT (SAFE)
# ======================================================
QUICK_GRADE_PLACEHOLDER = "Select a grade…"
QUICK_GRADE_CLEAR = "Clear selection"
QUICK_GRADE_OPTIONS = [
    QUICK_GRADE_PLACEHOLDER,
    "Gr 1-3", "Gr 4", "Gr 5", "Gr 6", "Gr 7",
    QUICK_GRADE_CLEAR
]

GRADE_TO_U_MAP = {
    "Gr 1-3": ["U7", "U8", "U9"],
    "Gr 4": ["U10"],
    "Gr 5": ["U11"],
    "Gr 6": ["U12"],
    "Gr 7": ["U13"],
}

# ======================================================
# QUERY PARAM HELPERS
# ======================================================
def qp_get(name, default=""):
    try:
        v = st.query_params.get(name, default)
    except Exception:
        v = default
    if isinstance(v, list):
        return v[0] if v else default
    return v

def qp_get_list(name):
    raw = qp_get(name, "")
    return [x.strip() for x in raw.split(",") if x.strip()]

def qp_set_from_state(payload):
    clean = {}
    for k, v in payload.items():
        if isinstance(v, list) and v:
            clean[k] = ",".join(v)
        elif isinstance(v, str) and v.strip():
            clean[k] = v
    st.query_params.from_dict(clean)

# ======================================================
# SESSION DEFAULTS
# ======================================================
def ss_init(k, v):
    if k not in st.session_state:
        st.session_state[k] = v

ss_init("screen_mode", "Events")
ss_init("view_mode", "All")
ss_init("cat_choice", [])
ss_init("act_choice", [])
ss_init("u_choice", [])
ss_init("gr_choice", [])
ss_init("search_text", "")

# Quick select safe state
ss_init("quick_grade_ui", QUICK_GRADE_PLACEHOLDER)
ss_init("_qg_applied", QUICK_GRADE_PLACEHOLDER)
ss_init("_pending_qg_reset", False)
ss_init("_request_rerun", False)
ss_init("_request_qp_sync", False)

# ======================================================
# INITIAL LOAD FROM URL (ONCE)
# ======================================================
if "qp_loaded" not in st.session_state:
    st.session_state.qp_loaded = True

    st.session_state.view_mode = qp_get("view", "All")
    st.session_state.cat_choice = qp_get_list("cat")
    st.session_state.act_choice = qp_get_list("act")
    st.session_state.u_choice = qp_get_list("u")
    st.session_state.gr_choice = qp_get_list("gr")
    st.session_state.search_text = qp_get("q", "")

    qg = qp_get("qg", QUICK_GRADE_PLACEHOLDER)
    if qg in QUICK_GRADE_OPTIONS:
        st.session_state.quick_grade_ui = qg
        st.session_state._qg_applied = QUICK_GRADE_PLACEHOLDER

# ======================================================
# LOAD DATA
# ======================================================
@st.cache_data(ttl=180)
def load_csv(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text), dtype=str).fillna("")

df = load_csv(UPCOMING_CSV_URL)
sub_df = load_csv(SUBMISSIONS_CSV_URL)

# ======================================================
# APPLY PENDING QUICK RESET (BEFORE WIDGET)
# ======================================================
if st.session_state._pending_qg_reset:
    st.session_state.quick_grade_ui = QUICK_GRADE_PLACEHOLDER
    st.session_state._qg_applied = QUICK_GRADE_PLACEHOLDER
    st.session_state._pending_qg_reset = False

# ======================================================
# HEADER
# ======================================================
st.markdown(
    f"""
<div style="background:#008080;padding:18px;border-radius:18px;color:white;text-align:center">
  <img src="{LOGO_URL}" style="max-width:820px;width:100%;background:white;padding:10px;border-radius:12px">
  <h2 style="margin:10px 0 0 0">Digital Hub</h2>
</div>
""",
    unsafe_allow_html=True,
)

# ======================================================
# TOP BAR
# ======================================================
left, mid, right = st.columns([2.2, 1, 1.2])

with left:
    st.selectbox(
        "Quick select",
        QUICK_GRADE_OPTIONS,
        key="quick_grade_ui",
        label_visibility="collapsed",
    )
    st.caption("Select a grade to auto-set Grade + Sport Age Group")

with mid:
    qg = st.session_state.quick_grade_ui
    if qg != st.session_state._qg_applied:

        if qg == QUICK_GRADE_CLEAR:
            st.session_state._pending_qg_reset = True
            st.session_state._qg_applied = QUICK_GRADE_CLEAR
            st.session_state._request_qp_sync = True
            st.session_state._request_rerun = True

        elif qg == QUICK_GRADE_PLACEHOLDER:
            st.session_state._qg_applied = qg

        else:
            if qg == "Gr 1-3":
                st.session_state.gr_choice = ["Gr 1", "Gr 2", "Gr 3"]
            else:
                st.session_state.gr_choice = [qg]

            st.session_state.u_choice = GRADE_TO_U_MAP.get(qg, [])
            st.session_state._qg_applied = qg
            st.session_state._request_qp_sync = True
            st.session_state._request_rerun = True

with right:
    if st.button("🔎 FILTER"):
        st.session_state.screen_mode = "Filter"
        st.rerun()

# ======================================================
# URL SYNC + SAFE RERUN
# ======================================================
if st.session_state._request_qp_sync:
    qp_set_from_state({
        "view": st.session_state.view_mode,
        "cat": st.session_state.cat_choice,
        "act": st.session_state.act_choice,
        "u": st.session_state.u_choice,
        "gr": st.session_state.gr_choice,
        "q": st.session_state.search_text,
        "qg": st.session_state.quick_grade_ui,
    })
    st.session_state._request_qp_sync = False

if st.session_state._request_rerun:
    st.session_state._request_rerun = False
    st.rerun()

# ======================================================
# VIEW RADIO
# ======================================================
st.radio(
    "Show",
    VIEW_OPTIONS,
    horizontal=True,
    key="view_mode",
)

# ======================================================
# EVENTS (MINIMAL SAFE VERSION)
# ======================================================
st.markdown("## 📅 Events")

if df.empty:
    st.info("No data available.")
else:
    for _, r in df.iterrows():
        st.markdown(
            f"""
<div style="border:1px solid #e5e7eb;border-radius:14px;padding:12px;margin-bottom:12px">
  <b>{r.get("Activity/Subject Name","")}</b><br>
  <span style="color:#64748b">{r.get("Date / Due Date","")}</span>
</div>
""",
            unsafe_allow_html=True,
        )

st.caption("LAERSKOOL MIDSTREAM COLLEGE PRIMARY · Digital Hub 2026")
