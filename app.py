import re
import io
import requests
import pandas as pd
import streamlit as st
from requests.exceptions import RequestException, Timeout

# 1. Basiese Opset
st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# 2. Styl (Midstream Maroon + Teal, selfde card feel)
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; font-family: Arial, sans-serif; }

    .nav-bar {
        background: linear-gradient(90deg, #6b0019, #0f5b66);
        color: white; padding: 18px; text-align: center;
        border-radius: 10px; margin-bottom: 16px;
        border: 2px solid rgba(255,255,255,0.28);
    }

    .card {
        background: white;
        padding: 18px;
        border-radius: 12px;
        border-left: 10px solid #6b0019;
        margin-bottom: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
    }

    .tag {
        background: #0f5b66;
        color: white;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: bold;
        display: inline-block;
    }

    .info {
        background: #e8f3f5;
        padding: 10px;
        border-radius: 10px;
        margin-top: 10px;
        border-left: 6px solid #6b0019;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

# Banner (jou file naam)
try:
    st.image("LMCP_RGB (1).png", use_container_width=True)
except Exception:
    pass

st.markdown('<div class="nav-bar"><h1 style="margin:0;">MIDSTREAM COLLEGE</h1><p style="margin:4px 0 0;">PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

# 3. Die Skakel
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# =============================
# Smart caching + timeout loader (NET DIT is nuut)
# =============================
@st.cache_data(ttl=300, show_spinner=False)
def load_sheet_csv(url: str) -> pd.DataFrame:
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=(5, 20))
    r.raise_for_status()

    text = r.text or ""
    if "<html" in text.lower():
        raise ValueError("Google returned HTML instead of CSV.")

    df = pd.read_csv(io.StringIO(text))
    df.columns = df.columns.str.strip()
    return df.fillna("")

# Sidebar: klein “refresh” link (nie lelik nie)
with st.sidebar:
    st.markdown("### Options")
    if st.button("Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# =============================
# Load data (netjiese errors)
# =============================
try:
    df = load_sheet_csv(URL)
except Timeout:
    st.error("Google is slow right now. Please try again.")
    st.stop()
except RequestException:
    st.error("Could not connect to Google Sheets right now.")
    st.stop()
except Exception as e:
    st.error("Something went wrong loading the sheet.")
    st.stop()

if df.empty:
    st.info("Waiting for data from the sheet…")
    st.stop()

# =============================
# STRICT column mapping (jou CSV)
# =============================
COL_CAT   = "Category"
COL_SUBJ  = "Activity/Subject Name"
COL_TEAM  = "Team"
COL_DATE  = "Date / Due Date"
COL_VEN   = "Venue"
COL_INFO  = "Information"
COL_GRADE = "Age Group (9,10) / Grade (1,2,3)"
COL_LINK  = "Programme / Document Link"

# =============================
# Filters (Category + Activity)
# =============================
cats = sorted([c for c in df[COL_CAT].astype(str).unique() if str(c).strip()])
sel_cat = st.multiselect("Category:", cats, default=[])

# Activity pull net uit selected Category(s)
df_cat = df.copy()
if sel_cat:
    df_cat = df_cat[df_cat[COL_CAT].astype(str).isin(sel_cat)]

acts = sorted([a for a in df_cat[COL_SUBJ].astype(str).unique() if str(a).strip()])
sel_act = st.selectbox("Activity:", ["All"] + acts)

# Apply filters
filtered = df.copy()
if sel_cat:
    filtered = filtered[filtered[COL_CAT].astype(str).isin(sel_cat)]
if sel_act != "All":
    filtered = filtered[filtered[COL_SUBJ].astype(str).eq(sel_act)]

# =============================
# Display cards (jou oorspronklike styl)
# =============================
for i in range(len(filtered)):
    row = filtered.iloc[i]

    c_cat   = str(row.get(COL_CAT, "")).strip()
    c_subj  = str(row.get(COL_SUBJ, "")).strip()
    c_team  = str(row.get(COL_TEAM, "")).strip()
    c_date  = str(row.get(COL_DATE, "")).strip()
    c_ven   = str(row.get(COL_VEN, "")).strip()
    c_info  = str(row.get(COL_INFO, "")).strip()
    c_grade = str(row.get(COL_GRADE, "")).strip()
    c_link  = str(row.get(COL_LINK, "")).strip()

    # Title rule: nie dubbel subject nie
    title = c_team if len(c_team) > 1 else c_subj

    st.markdown(f"""
    <div class="card">
        <span class="tag">{c_cat}</span>
        <div style="color:#0f5b66; font-weight:bold; margin-top:8px;">{c_subj}</div>
        <div style="font-size:1.2rem; font-weight:bold;">{title}</div>
        <div style="color:#555; font-size:14px;">
            {c_grade}<br>
            📅 {c_date}<br>
            📍 {c_ven}
        </div>
        {f'<div class="info">{c_info}</div>' if len(c_info) > 1 else ''}
    </div>
    """, unsafe_allow_html=True)

    if "http" in c_link:
        st.link_button("Document", c_link)
