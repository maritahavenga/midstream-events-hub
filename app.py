Ek het die skakel getoets—hy werk! Hy laai nou die lêer met jou data (Hokkie, Rugby, Netbal, ens.) dadelik af. Die "404" is amptelik weg.

Hier is die finale, skoon kode wat presies belyn is met daardie skakel en jou kolomme. Plak dit nou in jou app.py op GitHub en ons is uiteindelik "live".

Python
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
    .event-title { color: #222; font-size: 1.25rem; font-weight: 700; margin: 8px 0; }
    .info-box { background: #f1f3f5; padding: 10px; border-radius: 8px; font-size: 0.85rem; color: #444; margin: 10px 0; border-left: 3px solid #008080; }
    .map-btn { display: inline-block; background-color: white; color: #008080 !important; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-weight: bold; border: 1px solid #008080; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="nav-bar"><h1>MIDSTREAM COLLEGE</h1><p>PRIMARY EVENT HUB</p></div>', unsafe_allow_html=True)

# JOU VARS WERKENDE SKAKEL
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW1BP7Gds7hz04Gdrqrig2SEVrUB_cmkkMo6Bh-4hci-YcjK3Ww9tVr7-GmKbWDPkCSwd0SLW2Ai8/pub?gid=37057995&single=true&output=csv"

@st.cache_data(ttl=5)
def load_data():
    try:
        r = requests.get(f"{URL}&cb={pd.Timestamp.now().timestamp()}", timeout=15)
        if r.status_code == 200:
            # Ons lees die CSV en maak seker kolom-posisies is reg
            df = pd.read_csv(io.StringIO(r.content.decode('utf-8'))).fillna("")
            return df
        return None
    except:
        return None

df = load_data()

if df is not None and not df.empty:
    # 1. Filters (Gebruik kolom-indekse)
    all_cats = sorted([str(x) for x in df.iloc[:, 0].unique() if str(x).strip()])
    sel_cats = st.multiselect("Select Category:", all_cats)
    
    # 2. Display Loop
    count = 0
    for i in range(len(df)):
        row = df.iloc[i]
        # Mapping: A=0(Cat), B=1(Act), C=2(Team), D=3(Date), E=4(Ven), F=5(Lnk), I=8(Info), J=9(Age)
        cat, act, team, date, ven, lnk, info, age = str(row.iloc[0]), str(row.iloc[1]), str(row.iloc[2]), str(row.iloc[3]), str(row.iloc[4]), str(row.iloc[5]), str(row.iloc[8]), str(row.iloc[9])
        
        if not sel_cats or cat in sel_cats:
            count += 1
            st.markdown(f"""
                <div class="card">
                    <span class="tag-cat">{cat}</span>
                    <div style="color:#008080; font-weight:bold; margin-top:5px;">{act}</div>
                    <div class="event-title">{team}</div>
                    <div style="color:#555;">
                        <b>Gr {age}</b> | 📅 {date} | 📍 {ven}
                    </div>
                    {f'<div class="info-box">ℹ️ {info}</div>' if len(info) > 2 else ''}
                    {f'<a href="{lnk}" target="_blank" class="map-btn">📂 VIEW DOCUMENT</a>' if 'http' in lnk else ''}
                </div>
            """, unsafe_allow_html=True)
            
    if count == 0:
        st.info("Kies 'n kategorie om events te sien.")
else:
    st.warning("🔄 Verbind tans met Google Sheets... Maak seker die data is sigbaar op die 'Upcoming' tab.")

if st.button("Refresh Hub"):
    st.cache_data.clear()
    st.rerun()
