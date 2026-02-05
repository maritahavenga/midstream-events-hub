# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests, io, re
from datetime import datetime
from urllib.parse import urlparse

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="LMCP Hub",
    page_icon="📌",
    layout="wide",
)

# ============================================================
# REMOVE BACK ARROW / STREAMLIT NAV CONTROLS
# ============================================================
st.markdown(
    """
    <style>
    /* Remove top-left back arrow & nav */
    [data-testid="stSidebarNav"] { display: none; }
    [data-testid="stSidebarNavBack"] { display: none; }
    header button { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# CONFIG
# ============================================================
CSV_URL = st.secrets.get("CSV_URL", "") or st.sidebar.text_input(
    "CSV URL (published Google Sheet CSV)",
    value="",
)

# ============================================================
# HELPERS
# ============================================================
def cl(v):
    if v is None:
        return ""
    s = str(v).replace("\u00a0", " ").strip()
    s = re.sub(r"\.0$", "", s)
    if s.lower() in {"nan", "none"}:
        return ""
    return s

def is_valid_url(u):
    try:
        p = urlparse(u)
        return p.scheme in ("http", "https") and p.netloc
    except:
        return False

def parse_date_safe(x):
    try:
        return pd.to_datetime(cl(x), errors="coerce", dayfirst=True)
    except:
        return pd.NaT

def normalize_grade(g):
    g = cl(g).lower().replace("grade", "gr")
    m = re.search(r"gr\s*(\d+)", g)
    return f"gr {m.group(1)}" if m else g

def normalize_activity_for_display(activity, category, grade):
    a = cl(activity).lower()
    c = cl(category).lower()
    g = normalize_grade(grade)

    is_math = a in {"maths", "math", "mathematics", "mathematics / maths"}
    is_academic = c == "academics"
    is_4_7 = g in {"gr 4", "gr 5", "gr 6", "gr 7"}

    if (is_math or is_academic) and is_4_7:
        return "Mathematics / Maths"
    return cl(activity)

# ============================================================
# QUERY PARAM PERSISTENCE
# ============================================================
def qp_get(key, default=""):
    try:
        return st.query_params.get(key, default)
    except:
        return st.experimental_get_query_params().get(key, [default])[0]

def qp_set(params):
    clean = {k: v for k, v in params.items() if cl(v)}
    try:
        st.query_params.clear()
        st.query_params.update(clean)
    except:
        st.experimental_set_query_params(**clean)

# ============================================================
# LOAD DATA
# ============================================================
@st.cache_data(ttl=300)
def load_csv(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text))

if not CSV_URL:
    st.stop()

df = load_csv(CSV_URL)

# ============================================================
# COLUMN MAP
# ============================================================
COL_CATEGORY = "Category"
COL_ACTIVITY = "Activity/Subject Name"
COL_DATE = "Date / Due Date"
COL_GRADE = "Age Group (9,10) / Grade (1,2,3)"
COL_VENUE = "Venue"
COL_INFO = "Information"
COL_LINK = "Programme / Document Link"

for c in [COL_CATEGORY, COL_ACTIVITY, COL_DATE, COL_GRADE, COL_VENUE, COL_INFO, COL_LINK]:
    if c not in df.columns:
        df[c] = ""

df["_dt"] = df[COL_DATE].apply(parse_date_safe)

# ============================================================
# HEADER (NO BACK ARROW)
# ============================================================
st.title("LAERSKOOL MIDSTREAM COLLEGE PRIMARY")
st.subheader("Digital Hub")
st.markdown("---")

# ============================================================
# FILTER OPTIONS
# ============================================================
def opts(col):
    return sorted({cl(x) for x in df[col] if cl(x)}, key=str.lower)

category_opts = opts(COL_CATEGORY)
activity_opts = opts(COL_ACTIVITY)
grade_opts = opts(COL_GRADE)

# ============================================================
# FILTER STATE (NO DEFAULTS)
# ============================================================
if "f_cat" not in st.session_state:
    st.session_state.f_cat = qp_get("cat", "")
if "f_act" not in st.session_state:
    st.session_state.f_act = qp_get("act", "")
if "f_gr" not in st.session_state:
    st.session_state.f_gr = qp_get("gr", "")
if "view" not in st.session_state:
    st.session_state.view = qp_get("view", "Upcoming")

# ============================================================
# FILTER UI
# ============================================================
c1, c2, c3 = st.columns(3)

with c1:
    st.selectbox("Category", [""] + category_opts, key="f_cat")
with c2:
    st.selectbox("Activity", [""] + activity_opts, key="f_act")
with c3:
    st.selectbox("Age group / Grade / Class", [""] + grade_opts, key="f_gr")

b1, b2, _ = st.columns([1, 1, 4])

with b1:
    if st.button("💾 Save filters", use_container_width=True):
        qp_set({
            "cat": st.session_state.f_cat,
            "act": st.session_state.f_act,
            "gr": st.session_state.f_gr,
            "view": st.session_state.view,
        })

with b2:
    if st.button("🧹 Clear filters", use_container_width=True):
        st.session_state.f_cat = ""
        st.session_state.f_act = ""
        st.session_state.f_gr = ""
        qp_set({})
        st.rerun()

st.markdown("---")

# ============================================================
# APPLY FILTERS
# ============================================================
f = df.copy()

if st.session_state.f_cat:
    f = f[f[COL_CATEGORY] == st.session_state.f_cat]
if st.session_state.f_act:
    f = f[f[COL_ACTIVITY] == st.session_state.f_act]
if st.session_state.f_gr:
    f = f[f[COL_GRADE] == st.session_state.f_gr]

f = f.sort_values("_dt", na_position="last")

# ============================================================
# RENDER CARDS
# ============================================================
for _, r in f.iterrows():
    activity = normalize_activity_for_display(
        r[COL_ACTIVITY],
        r[COL_CATEGORY],
        r[COL_GRADE]
    )

    date_txt = r["_dt"].strftime("%a, %d %b %Y") if pd.notna(r["_dt"]) else "-"

    st.markdown(
        f"""
        <div style="border:1px solid rgba(255,255,255,0.12);
                    border-radius:14px;
                    padding:14px;
                    margin-bottom:12px;">
            <div style="font-size:18px;font-weight:800;">{activity}</div>
            <div style="font-size:13px;opacity:.8;">
                {r[COL_CATEGORY]} | {r[COL_GRADE]}
            </div>
            <div style="margin-top:6px;"><b>Date:</b> {date_txt}</div>
            <div><b>Venue:</b> {cl(r[COL_VENUE]) or "-"}</div>
            {f"<div style='margin-top:6px;'>{r[COL_INFO]}</div>" if cl(r[COL_INFO]) else ""}
            {f"<a href='{r[COL_LINK]}' target='_blank'>📎 Open document</a>" if is_valid_url(r[COL_LINK]) else ""}
        </div>
        """,
        unsafe_allow_html=True
    )

if len(f) == 0:
    st.info("No items match your filters.")

st.markdown("---")
st.caption("Filters only persist after clicking **Save filters**. Use **Clear filters** to reset.")
