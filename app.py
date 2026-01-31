import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# --- UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .nav-bar { background: linear-gradient(135deg, #800000 0%, #a00000 100%); color: white; padding: 25px; text-align: center; border-radius: 0 0 20px 20px; margin-top: -60px; }
    .card { background: white; padding: 20px; border-radius: 15px; border-left: 10px solid #800000; margin-top: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .whole-term-card { border-left: 10px solid #FFD700 !important; background-color: #fffdf0 !important; }
    .tag-cat { background: #800000; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }
    .event-title { color: #222; font-size: 1.2rem; font-weight: 700; margin: 5px 0; }
    .info-box { background: #f1f3f5; padding: 10px; border-radius: 8px; font-size: 0.85rem; color: #444; margin: 10px 0; border-left: 3px solid #008080; white-space: pre-wrap; }
    .map-btn { display: inline-block; background-color: white; color: #008080 !important; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-weight: bold; border: 1px solid #008080; margin-top: 5px; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

# JOU SKAKEL WAT ONS WEET WERK
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

@st.cache_data(ttl=1)
def load_data():
    try:
        # Ons gebruik 'n eenvoudige GET sonder te veel parameters wat Google verwar
        r = requests.get(URL, timeout=10)
        # As Google HTML stuur, probeer ons dit hanteer
        if "<!DOCTYPE" in r.text:
            return "HTML_WAIT"
        df = pd.read_csv(io.StringIO(r.text)).fillna("")
        return df
    except:
        return None

df = load_data()

if isinstance(df, str) and df == "HTML_WAIT":
    st.warning("🔄 Google se bediener verfris tans... Verfris asb die app oor 10 sekondes.")
    if st.button("Probeer nou weer"):
        st.cache_data.clear()
        st.rerun()
elif df is not None and not df.empty:
    # FILTERS
    all_cats = sorted([str(x) for x in df.iloc[:, 0].unique() if str(x).strip()])
    sel_cats = st.multiselect("Select Category:", all_cats)
    
    all_grades = sorted([str(x) for x in df.iloc[:, 9].unique() if str(x).strip()])
    sel_grades = st.multiselect("Filter by Grade:", all_grades)

    for i in range(len(df)):
        row = df.iloc[i]
        
        # JOU KOLOMME (A=0 tot K=10)
        cat   = str(row.iloc[0])  # A
        subj  = str(row.iloc[1])  # B
        asses = str(row.iloc[2])  # C
        date  = str(row.iloc[3])  # D
        ven   = str(row.iloc[4])  # E
        lnk   = str(row.iloc[5])  # F
        team  = str(row.iloc[6])  # G
        info  = str(row.iloc[7])  # H
        grade = str(row.iloc[9])  # J
        dur   = str(row.iloc[10]) # K

        # Titellogika: Wys Team as daar een is, anders Assessment/Subject
        display_title = team if len(team) > 1 else (asses if len(asses) > 1 else subj)
        is_whole = "whole term" in dur.lower() or "whole term" in date.lower()

        if (not sel_cats or cat in sel_cats) and (not sel_grades or grade in sel_grades):
            card_class = "card whole-term-card" if is_whole else "card"
            st.markdown(f"""
                <div class="{card_class}">
                    <span class="tag-cat">{cat}</span>
                    <div style="color:#008080; font-weight:bold; margin-top:5px;">{subj}</div>
                    <div class="event-title">{display_title}</div>
                    <div style="color:#555; font-size:0.9rem;">
                        <b>Grade: {grade}</b> | 📅 {date} | 📍 {ven}
                    </div>
                    {f'<div class="info-box">ℹ️ {info}</div>' if len(info) > 1 else ''}
                    {f'<a href="{lnk}" target="_blank" class="map-btn">📂 VIEW DOCUMENT</a>' if 'http' in lnk else ''}
                </div>
            """, unsafe_allow_html=True)
else:
    st.info("🔄 Connecting... If this takes too long, make sure there is data on your 'Upcoming' tab.")
