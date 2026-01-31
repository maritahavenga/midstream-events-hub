import streamlit as st
import pandas as pd

import re
import io
import requests
from requests.exceptions import RequestException, Timeout

# 1) Basiese Opset (sidebar collapsed)
st.set_page_config(page_title="LMCP Event Hub", layout="centered", initial_sidebar_state="collapsed")

# 2) Styl (jou oorspronklike)
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .nav-bar { background-color: #800000; color: white; padding: 20px; text-align: center; border-radius: 10px; margin-bottom: 20px; }
    .card { background: white; padding: 20px; border-radius: 12px; border-left: 10px solid #800000; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .tag { background: #800000; color: white; padding: 3px 10px; border-radius: 5px; font-size: 11px; font-weight: bold; }
    .info { background: #f1f3f5; padding: 10px; border-radius: 5px; margin-top: 10px; border-left: 3px solid #008080; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

# 3) Skakel (Upcoming tab)
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# =============================
# Anti-crash loader: timeout + cache + error handling
# =============================
@st.cache_data(ttl=300, show_spinner=False)  # 5 minute cache
def load_sheet_csv(url: str) -> pd.DataFrame:
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=(5, 20))
    r.raise_for_status()

    text = r.text or ""
    if "<html" in text.lower():
        raise ValueError("Google returned HTML instead of CSV (publish/share issue).")

    df = pd.read_csv(io.StringIO(text)).fillna("")
    df.columns = df.columns.str.strip()
    return df

try:
    df = load_sheet_csv(URL)
except Timeout:
    st.error("Kon nie tans met Google Sheets koppel nie (timeout). Probeer later weer.")
    st.stop()
except RequestException:
    st.error("Kon nie tans met Google Sheets koppel nie (connection). Probeer later weer.")
    st.stop()
except Exception as e:
    st.error("Kon nie tans met Google Sheets koppel nie.")
    with st.expander("Technical details"):
        st.code(str(e))
    st.stop()

if df.empty:
    st.info("Wagtend op data vanaf die 'Upcoming' tab...")
    st.stop()

# =============================
# Kolom name mapping (NO MORE iloc -> no more 'spring')
# =============================
COL_CAT   = "Category"
COL_SUBJ  = "Activity/Subject Name"
COL_DATE  = "Date / Due Date"
COL_VEN   = "Venue"
COL_LINK  = "Programme / Document Link"
COL_TEAM  = "Team"
COL_INFO  = "Information"
COL_GRADE = "Age Group (9,10) / Grade (1,2,3)"

# Kategorie filter
cats = sorted([str(c).strip() for c in df[COL_CAT].astype(str).unique() if str(c).strip()])
sel_cat = st.multiselect("Kies Kategorie:", cats)

# Wys cards
for _, row in df.iterrows():
    c_cat   = str(row.get(COL_CAT, "")).strip()
    c_subj  = str(row.get(COL_SUBJ, "")).strip()
    c_date  = str(row.get(COL_DATE, "")).strip()
    c_ven   = str(row.get(COL_VEN, "")).strip()
    c_link  = str(row.get(COL_LINK, "")).strip()
    c_team  = str(row.get(COL_TEAM, "")).strip()
    c_info  = str(row.get(COL_INFO, "")).strip()
    c_grade = str(row.get(COL_GRADE, "")).strip()

    if sel_cat and c_cat not in sel_cat:
        continue

    title = c_team if len(c_team) > 1 else c_subj

    st.markdown(f"""
    <div class="card">
        <span class="tag">{c_cat}</span>
        <div style="color:#008080; font-weight:bold; margin-top:8px;">{c_subj}</div>
        <div style="font-size:1.2rem; font-weight:bold;">{title}</div>
        <div style="color:#555; font-size:14px;">
            {c_grade}<br>
            📅 {c_date}<br>
            📍 {c_ven}
        </div>
        {f'<div class="info">{c_info}</div>' if len(c_info)>1 else ''}
    </div>
    """, unsafe_allow_html=True)

    if "http" in c_link:
        st.link_button("Document", c_link)
