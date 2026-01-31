import streamlit as st
import pandas as pd
import requests, io
import time

st.set_page_config(page_title="LMCP Event Hub", layout="centered")

# --- UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .nav-bar { background: linear-gradient(135deg, #800000 0%, #a00000 100%); color: white; padding: 25px; text-align: center; border-radius: 0 0 20px 20px; margin-top: -60px; }
    .card { background: white; padding: 20px; border-radius: 15px; border-left: 10px solid #800000; margin-top: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .tag-cat { background: #800000; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }
    .event-title { color: #222; font-size: 1.2rem; font-weight: 700; margin: 5px 0; }
    .info-box { background: #f1f3f5; padding: 10px; border-radius: 8px; font-size: 0.85rem; color: #444; margin: 10px 0; border-left: 3px solid #008080; white-space: pre-wrap; }
    .map-btn { display: inline-block; background-color: white; color: #008080 !important; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-weight: bold; border: 1px solid #008080; margin-top: 5px; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

# JOU WERKWERKENDE SKAKEL
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

# ONS HAAL DIE CACHE HEELTEMAL UIT VIR 'N VARS RESET
try:
    # Dwing Google om die varsste data te stuur
    r = requests.get(f"{URL}&timestamp={time.time()}", timeout=15)
    df = pd.read_csv(io.StringIO(r.text)).fillna("")
    
    if not df.empty:
        # Filters
        all_cats = sorted([str(x) for x in df.iloc[:, 0].unique() if str(x).strip()])
        sel_cats = st.multiselect("Filter op Kategorie:", all_cats)
        
        all_grades = sorted([str(x) for x in df.iloc[:, 9].unique() if str(x).strip()])
        sel_grades = st.multiselect("Filter op Graad:", all_grades)

        for i in range(len(df)):
            row = df.iloc[i]
            # Mapping: A=0, B=1, C=2, D=3, E=4, F=5, G=6, H=7, J=9
            cat   = str(row.iloc[0])
            subj  = str(row.iloc[1])
            asses = str(row.iloc[2])
            date  = str(row.iloc[3])
            ven   = str(row.iloc[4])
            lnk   = str(row.iloc[5])
            team  = str(row.iloc[6])
            info  = str(row.iloc[7])
            grade = str(row.iloc[9])
            
            display_title = team if len(team) > 1 else (asses if len(asses) > 1 else subj)

            if (not sel_cats or cat in sel_cats) and (not sel_grades or grade in sel_grades):
                st.markdown(f"""
                    <div class="card">
                        <span class="tag-cat">{cat}</span>
                        <div style="color:#008080; font-weight:bold; margin-top:5px;">{subj}</div>
                        <div class="event-title">{display_title}</div>
                        <div style="color:#555; font-size:0.9rem;">
                            <b>Grade {grade}</b> | 📅 {date} | 📍 {ven}
                        </div>
                        {f'<div class="info-box">ℹ️ {info}</div>' if len(info) > 2 else ''}
                        {f'<a href="{lnk}" target="_blank" class="map-btn">📂 OOP DOKUMENT</a>' if 'http' in lnk else ''}
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Geen data gevind op die 'Upcoming' tab nie.")

except Exception as e:
    st.error(f"Fout met die aflaai van data: {e}")

if st.button("Verfris Hub"):
    st.rerun()
