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
    .tag-cat { background: #800000; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }
    .event-title { color: #222; font-size: 1.2rem; font-weight: 700; margin: 5px 0; }
    .info-box { background: #f1f3f5; padding: 10px; border-radius: 8px; font-size: 0.85rem; color: #444; margin: 10px 0; border-left: 3px solid #008080; white-space: pre-wrap; }
    .map-btn { display: inline-block; background-color: white; color: #008080 !important; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-weight: bold; border: 1px solid #008080; margin-top: 5px; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

# JOU NUWE WERKWERKENDE CSV-SKAKEL
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

@st.cache_data(ttl=2)
def load_data():
    try:
        r = requests.get(f"{URL}&cb={pd.Timestamp.now().timestamp()}", timeout=15)
        if r.status_code == 200:
            # Lees CSV en vul leë spasies
            df = pd.read_csv(io.StringIO(r.content.decode('utf-8'))).fillna("")
            return df
        return None
    except:
        return None

df = load_data()

if df is not None and not df.empty:
    # 1. Filters (Kategorie in Kolom A, Graad in Kolom J)
    all_cats = sorted([str(x) for x in df.iloc[:, 0].unique() if str(x).strip()])
    sel_cats = st.multiselect("Select Category:", all_cats)
    
    all_grades = sorted([str(x) for x in df.iloc[:, 9].unique() if str(x).strip()])
    sel_grades = st.multiselect("Filter by Grade:", all_grades)

    # 2. Display Loop
    count = 0
    for i in range(len(df)):
        row = df.iloc[i]
        
        # Mapping gebaseer op jou lys: A=0, B=1, C=2, D=3, E=4, F=5, G=6, H=7, J=9
        cat   = str(row.iloc[0])  # A
        subj  = str(row.iloc[1])  # B
        asses = str(row.iloc[2])  # C
        date  = str(row.iloc[3])  # D
        ven   = str(row.iloc[4])  # E
        lnk   = str(row.iloc[5])  # F
        team  = str(row.iloc[6])  # G
        info  = str(row.iloc[7])  # H
        grade = str(row.iloc[9])  # J
        
        # Titel prioriteit: Team -> Assessment -> Subject
        display_title = team if len(team) > 1 else (asses if len(asses) > 1 else subj)

        if (not sel_cats or cat in sel_cats) and (not sel_grades or grade in sel_grades):
            count += 1
            st.markdown(f"""
                <div class="card">
                    <span class="tag-cat">{cat}</span>
                    <div style="color:#008080; font-weight:bold; margin-top:5px;">{subj}</div>
                    <div class="event-title">{display_title}</div>
                    <div style="color:#555; font-size:0.9rem;">
                        <b>Grade {grade}</b> | 📅 {date} | 📍 {ven}
                    </div>
                    {f'<div class="info-box">ℹ️ {info}</div>' if len(info) > 2 else ''}
                    {f'<a href="{lnk}" target="_blank" class="map-btn">📂 VIEW DOCUMENT</a>' if 'http' in lnk else ''}
                </div>
            """, unsafe_allow_html=True)
    
    if count == 0:
        st.info("No events found for the selected filters.")
else:
    st.warning("🔄 Connecting to the event hub... Please ensure the 'Upcoming' tab in your Sheet has data.")

if st.button("Refresh Now"):
    st.cache_data.clear()
    st.rerun()
