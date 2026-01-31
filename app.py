import streamlit as st
import pandas as pd

import requests, io
from requests.exceptions import RequestException, Timeout

st.set_page_config(page_title="LMCP Event Hub", layout="centered", initial_sidebar_state="collapsed")

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

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrigq2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

@st.cache_data(ttl=300, show_spinner=False)
def load_sheet_csv(url: str) -> pd.DataFrame:
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=(5, 20))
    r.raise_for_status()

    text = r.text or ""
    if "<html" in text.lower():
        raise ValueError("Google returned HTML instead of CSV.")

    df = pd.read_csv(io.StringIO(text)).fillna("")
    return df

try:
    df = load_sheet_csv(URL)
except Timeout:
    st.error("Kon nie tans met Google Sheets koppel nie. Probeer later weer.")
    st.stop()
except RequestException:
    st.error("Kon nie tans met Google Sheets koppel nie. Probeer later weer.")
    st.stop()
except Exception:
    st.error("Kon nie tans met Google Sheets koppel nie.")
    st.stop()

if df.empty:
    st.info("Wagtend op data vanaf die 'Upcoming' tab...")
    st.stop()

cats = sorted(df.iloc[:, 0].unique())
sel_cat = st.multiselect("Kies Kategorie:", cats)

for i in range(len(df)):
    row = df.iloc[i]

    c_cat   = str(row.iloc[0])
    c_subj  = str(row.iloc[1])
    c_date  = str(row.iloc[3])
    c_ven   = str(row.iloc[4])
    c_link  = str(row.iloc[5])
    c_team  = str(row.iloc[6])
    c_info  = str(row.iloc[8])
    c_grade = str(row.iloc[9])

    if not sel_cat or c_cat in sel_cat:
        st.markdown(f"""
        <div class="card">
            <span class="tag">{c_cat}</span>
            <div style="color:#008080; font-weight:bold; margin-top:8px;">{c_subj}</div>
            <div style="font-size:1.2rem; font-weight:bold;">{c_team if len(c_team)>1 else c_subj}</div>
            <div style="color:#555; font-size:14px;">{c_grade} | 📅 {c_date} | 📍 {c_ven}</div>
            {f'<div class="info">{c_info}</div>' if len(c_info)>1 else ''}
        </div>
        """, unsafe_allow_html=True)

        if "http" in c_link:
            st.link_button("Document", c_link)
